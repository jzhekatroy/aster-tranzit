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
    
    // Скрываем предыдущие сообщения
    hideMessages();
    
    // Показываем загрузку
    document.getElementById('loading').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    
    // Создаем FormData
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            currentResults = data.mappings;
            displayResults(data);
            showSuccess(`Успешно обработано ${data.total} номеров (новых: ${data.new}, существующих: ${data.existing})`);
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

// Отображение результатов
function displayResults(data) {
    document.getElementById('totalCount').textContent = data.total;
    document.getElementById('newCount').textContent = data.new;
    document.getElementById('existingCount').textContent = data.existing;
    
    const tbody = document.getElementById('resultsBody');
    tbody.innerHTML = '';
    
    data.mappings.forEach((mapping, index) => {
        const row = document.createElement('tr');
        const statusBadge = mapping.status === 'new' 
            ? '<span class="badge badge-new">Новый</span>'
            : '<span class="badge badge-existing">Существующий</span>';
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${mapping.real_phone}</td>
            <td><strong>${mapping.fake_phone}</strong></td>
            <td>${statusBadge}</td>
        `;
        tbody.appendChild(row);
    });
    
    document.getElementById('resultsSection').style.display = 'block';
}

// Загрузка всех маппингов
async function loadAllMappings() {
    try {
        const response = await fetch('/mappings');
        const data = await response.json();
        
        if (response.ok && data.success) {
            const tbody = document.getElementById('allMappingsBody');
            tbody.innerHTML = '';
            
            if (data.mappings.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Нет сохраненных номеров</td></tr>';
            } else {
                data.mappings.forEach((mapping, index) => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${mapping.real_phone}</td>
                        <td><strong>${mapping.fake_phone}</strong></td>
                        <td>${new Date(mapping.created_at).toLocaleString('ru-RU')}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
            
            document.getElementById('allMappings').style.display = 'block';
        } else {
            showError(data.error || 'Ошибка при загрузке данных');
        }
    } catch (error) {
        showError('Ошибка соединения с сервером: ' + error.message);
    }
}

// Экспорт текущих результатов
function exportResults() {
    if (currentResults.length === 0) {
        showError('Нет данных для экспорта');
        return;
    }
    
    let csv = 'Real Phone,Fake Phone,Status\n';
    currentResults.forEach(mapping => {
        csv += `${mapping.real_phone},${mapping.fake_phone},${mapping.status}\n`;
    });
    
    downloadCSV(csv, 'phone_mappings_results.csv');
}

// Экспорт всех маппингов
async function exportAllMappings() {
    try {
        window.location.href = '/export/csv';
    } catch (error) {
        showError('Ошибка при экспорте: ' + error.message);
    }
}

// Копирование фейковых номеров в буфер обмена
function copyToClipboard() {
    if (currentResults.length === 0) {
        showError('Нет данных для копирования');
        return;
    }
    
    const fakePhones = currentResults.map(m => m.fake_phone).join('\n');
    
    navigator.clipboard.writeText(fakePhones).then(() => {
        showSuccess('Фейковые номера скопированы в буфер обмена');
    }).catch(err => {
        showError('Ошибка копирования: ' + err.message);
    });
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

// Показ успеха
function showSuccess(message) {
    const successDiv = document.getElementById('success');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    
    // Автоматически скрыть через 5 секунд
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 5000);
}

// Скрыть все сообщения
function hideMessages() {
    document.getElementById('error').style.display = 'none';
    document.getElementById('success').style.display = 'none';
}

