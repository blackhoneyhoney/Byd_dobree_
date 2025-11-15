document.addEventListener('DOMContentLoaded', function() {
    // Элементы формы
    const textarea = document.getElementById('text');
    const videoTypeSelect = document.getElementById('video-type');
    const timeVideoSelect = document.getElementById('time-video');
    const generateStoryboardCheckbox = document.getElementById('generate-storyboard');
    const generateBtn = document.querySelector('.btn-generate');
    const loadingDiv = document.getElementById('loading');
    const resultsSection = document.getElementById('results-section');
    const generatedText = document.getElementById('generated-text');
    const storyboardSection = document.getElementById('storyboard-section');
    const generatedStoryboard = document.getElementById('generated-storyboard');
    
    // Кнопки авторизации
    const loginBtn = document.querySelector('.btn-login');
    const registerBtn = document.querySelector('.btn-register');

    // Обработчик кнопки генерации
    generateBtn.addEventListener('click', async function(e) {
        e.preventDefault();

        const prompt = textarea.value.trim();
        const videoType = videoTypeSelect.value;
        const duration = parseInt(timeVideoSelect.value);
        const generateStoryboard = generateStoryboardCheckbox.checked;

        // Валидация
        if (!prompt) {
            showError('Пожалуйста, введите описание видео');
            return;
        }
        if (!videoType) {
            showError('Пожалуйста, выберите тип видео');
            return;
        }
        if (!duration) {
            showError('Пожалуйста, выберите длительность видео');
            return;
        }

        // Скрываем предыдущие результаты и ошибки
        resultsSection.classList.remove('active');
        storyboardSection.style.display = 'none';
        hideError();
        
        // Показываем загрузку
        loadingDiv.classList.add('active');
        generateBtn.disabled = true;
        generateBtn.textContent = 'Генерация...';

        // Таймаут 60 секунд
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Время генерации истекло (60 секунд)')), 60000)
        );

        try {
            const fetchPromise = fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    video_type: videoType,
                    duration: duration,
                    generate_storyboard: generateStoryboard
                })
            });

            const response = await Promise.race([fetchPromise, timeoutPromise]);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка сервера');
            }

            // Отображаем результаты
            generatedText.textContent = data.script || 'Сценарий успешно сгенерирован!';
            resultsSection.classList.add('active');
            
            // Если есть раскадровка
            if (data.storyboard) {
                generatedStoryboard.textContent = data.storyboard;
                storyboardSection.style.display = 'block';
            } else {
                storyboardSection.style.display = 'none';
            }
            
            // Прокручиваем к результатам
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            showError(error.message);
        } finally {
            // Убираем загрузку
            loadingDiv.classList.remove('active');
            generateBtn.disabled = false;
            generateBtn.textContent = 'Сгенерировать видео';
        }
    });

    // Обработчики кнопок авторизации
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            // Здесь можно добавить логику входа
            alert('Функция входа будет реализована позже');
        });
    }

    if (registerBtn) {
        registerBtn.addEventListener('click', function() {
            // Здесь можно добавить логику регистрации
            alert('Функция регистрации будет реализована позже');
        });
    }

    // Функция показа ошибки
    function showError(message) {
        // Создаем или находим элемент для ошибки
        let errorDiv = document.getElementById('error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'error-message';
            errorDiv.className = 'error-message';
            // Вставляем после секции генерации
            const generationSection = document.querySelector('.generation-section');
            generationSection.parentNode.insertBefore(errorDiv, generationSection.nextSibling);
        }
        errorDiv.textContent = 'Ошибка: ' + message;
        errorDiv.classList.add('active');
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            hideError();
        }, 5000);
    }

    // Функция скрытия ошибки
    function hideError() {
        const errorDiv = document.getElementById('error-message');
        if (errorDiv) {
            errorDiv.classList.remove('active');
        }
    }
});

