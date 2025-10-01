// Глобальная переменная для хранения результатов
let currentResults = [];

// Обработка загрузки формы
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Пожалуйста, выберите файл');
        return;
    }
    
    // Скрываем предыдущие элементы
    document.getElementById('error').style.display = 'none';
    document.getElementById('downloadSection').style.display = 'none';
    document.getElementById('listSection').style.display = 'none';
    
    // Показываем загрузку
    document.getElementById('loading').style.display = 'block';
    
    // Создаем FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('clear_old', 'true'); // Флаг для очистки базы
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            currentResults = data.mappings;
            
            // Показываем кнопку скачать
            document.getElementById('downloadSection').style.display = 'block';
            
            // Показываем список
            displayList(data.mappings);
            
            fileInput.value = ''; // Очистка input
        } else {
            showError(data.error || 'Ошибка при обработке файла');
        }
    } catch (error) {
        showError('Ошибка соединения с сервером: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

// Обновление текста при выборе файла
document.getElementById('fileInput').addEventListener('change', (e) => {
    const fileName = e.target.files[0]?.name;
    if (fileName) {
        document.querySelector('.file-text').textContent = fileName;
    }
});

// Отображение списка номеров
function displayList(mappings) {
    const tbody = document.getElementById('phoneListBody');
    tbody.innerHTML = '';
    
    document.getElementById('phoneCount').textContent = mappings.length;
    
    mappings.forEach((mapping) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${mapping.real_phone}</td>
            <td><strong>${mapping.fake_phone}</strong></td>
        `;
        tbody.appendChild(row);
    });
    
    document.getElementById('listSection').style.display = 'block';
}

// Скачать результаты
function downloadResults() {
    if (currentResults.length === 0) {
        showError('Нет данных для скачивания');
        return;
    }
    
    let csv = 'Real Phone,Fake Phone\n';
    currentResults.forEach(mapping => {
        csv += `${mapping.real_phone},${mapping.fake_phone}\n`;
    });
    
    downloadCSV(csv, 'phone_mappings.csv');
}

// Скачивание CSV
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Показ ошибки
function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Автоматически скрыть через 5 секунд
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

