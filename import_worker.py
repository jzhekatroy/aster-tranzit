import csv
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from threading import Lock, Thread

from flask import Flask, jsonify

from app.models import Database
from app.utils import normalize_phone, validate_phone
from config import Config


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "import.log"
TARGET_FILE_NAME = "GGS_all_phones.csv"


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )


class ImportState:
    """Потокобезопасное хранение статуса последнего импорта."""

    def __init__(self):
        self._lock = Lock()
        self._data = None

    def set(self, data):
        with self._lock:
            self._data = data

    def snapshot(self):
        with self._lock:
            return dict(self._data) if self._data else None


class ImportWorker:
    def __init__(self, state: ImportState):
        self.state = state
        self.db = Database()
        incoming = Path(Config.INCOMING_DIR)
        archive = Path(Config.ARCHIVE_DIR)
        self.incoming_dir = incoming if incoming.is_absolute() else (BASE_DIR / incoming).resolve()
        self.archive_dir = archive if archive.is_absolute() else (BASE_DIR / archive).resolve()
        self.scan_interval = Config.SCAN_INTERVAL
        self.max_file_bytes = Config.MAX_FILE_BYTES

        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Создаем таблицы, если их ещё нет
        self.db.create_tables()

    def run_forever(self):
        while True:
            try:
                self.scan_once()
            except Exception as e:
                logging.exception(f"Необработанная ошибка цикла: {e}")
            time.sleep(self.scan_interval)

    def scan_once(self):
        target = self.incoming_dir / TARGET_FILE_NAME
        if not target.exists():
            return

        processing_path = target.with_suffix(target.suffix + ".processing")
        try:
            target.rename(processing_path)
        except FileNotFoundError:
            return

        started_at = datetime.utcnow()
        status_report = {
            "file": TARGET_FILE_NAME,
            "started_at": started_at.isoformat() + "Z",
        }

        try:
            insert_count, total_rows = self.process_file(processing_path)
            finished_at = datetime.utcnow()
            duration = (finished_at - started_at).total_seconds()
            status_report.update(
                {
                    "success": True,
                    "inserted": insert_count,
                    "total_rows": total_rows,
                    "duration_sec": duration,
                    "finished_at": finished_at.isoformat() + "Z",
                }
            )
            self.write_marker(True, status_report)
            logging.info(
                f"Импорт завершен: inserted={insert_count}, total={total_rows}, "
                f"duration={duration:.2f}s"
            )
        except Exception as e:
            finished_at = datetime.utcnow()
            duration = (finished_at - started_at).total_seconds()
            status_report.update(
                {
                    "success": False,
                    "error": str(e),
                    "duration_sec": duration,
                    "finished_at": finished_at.isoformat() + "Z",
                }
            )
            self.write_marker(False, status_report)
            logging.error(f"Импорт завершился с ошибкой: {e}")

        # Архивируем исходный файл вне зависимости от результата
        archive_name = (
            f"{Path(TARGET_FILE_NAME).stem}_{finished_at.strftime('%Y%m%d_%H%M%S')}"
            f"{Path(TARGET_FILE_NAME).suffix}"
        )
        archive_path = self.archive_dir / archive_name
        try:
            shutil.move(processing_path, archive_path)
        except Exception as move_error:
            logging.error(f"Не удалось переместить файл в архив: {move_error}")

        self.state.set(status_report)

    def process_file(self, path: Path):
        """Прочитать CSV, валидировать и заменить данные в БД."""
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")

        size_bytes = path.stat().st_size
        if size_bytes > self.max_file_bytes:
            raise ValueError(
                f"Файл слишком большой: {size_bytes} байт > {self.max_file_bytes}"
            )

        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=";")
            rows = list(reader)

        if not rows:
            raise ValueError("Файл пуст")

        # Пропускаем заголовок
        data_rows = rows[1:]
        if not data_rows:
            raise ValueError("Нет данных после заголовка")

        mappings = []
        seen_real = set()
        seen_fake = set()

        for idx, row in enumerate(data_rows, start=2):  # старт с 2 из-за заголовка
            if len(row) < 2:
                raise ValueError(f"Недостаточно колонок в строке {idx}")

            raw_real, raw_fake = row[0].strip(), row[1].strip()
            if not raw_real or not raw_fake:
                raise ValueError(f"Пустое значение в строке {idx}")

            real_phone = normalize_phone(raw_real)
            fake_phone = normalize_phone(raw_fake)

            if not validate_phone(real_phone):
                raise ValueError(f"Невалидный real_phone в строке {idx}: {raw_real}")
            if not validate_phone(fake_phone):
                raise ValueError(f"Невалидный fake_phone в строке {idx}: {raw_fake}")

            if real_phone in seen_real:
                raise ValueError(f"Дубликат real_phone '{real_phone}' в строке {idx}")
            if fake_phone in seen_fake:
                raise ValueError(f"Дубликат fake_phone '{fake_phone}' в строке {idx}")

            seen_real.add(real_phone)
            seen_fake.add(fake_phone)
            mappings.append((real_phone, fake_phone))

        success, error, inserted = self.db.replace_all_mappings(mappings)
        if not success:
            raise ValueError(f"Ошибка записи в БД: {error}")

        return inserted, len(data_rows)

    def write_marker(self, success: bool, report: dict):
        """Записать файл результата .OK или .fail рядом с входным файлом."""
        suffix = ".OK" if success else ".fail"
        marker_path = self.incoming_dir / f"{TARGET_FILE_NAME}{suffix}"

        lines = [
            f"file={report.get('file')}",
            f"success={report.get('success')}",
            f"started_at={report.get('started_at')}",
            f"finished_at={report.get('finished_at')}",
            f"duration_sec={report.get('duration_sec')}",
        ]

        if success:
            lines.append(f"total_rows={report.get('total_rows')}")
            lines.append(f"inserted={report.get('inserted')}")
        else:
            lines.append(f"error={report.get('error')}")

        try:
            with open(marker_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception as e:
            logging.error(f"Не удалось записать файл статуса {marker_path}: {e}")


def create_status_app(state: ImportState):
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/status")
    def status():
        snap = state.snapshot()
        if not snap:
            return jsonify({"status": "idle"}), 200
        return jsonify({"status": "ok", "last_run": snap}), 200

    return app


def main():
    setup_logging()
    state = ImportState()
    worker = ImportWorker(state)

    # Запускаем воркер в отдельном потоке
    Thread(target=worker.run_forever, daemon=True).start()

    # Минимальный статус-сервер на 3000 (по умолчанию)
    app = create_status_app(state)
    app.run(host=Config.HOST, port=Config.PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()

