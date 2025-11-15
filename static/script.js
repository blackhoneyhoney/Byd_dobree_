document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('promptForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const scriptContent = document.getElementById('scriptContent');
    const storyboardSection = document.getElementById('storyboardSection');
    const storyboardContent = document.getElementById('storyboardContent');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const prompt = document.getElementById('prompt').value.trim();
        const generateStoryboard = document.getElementById('generateStoryboard').checked;
        const videoType = document.getElementById('videoType').value;
        const duration = document.getElementById('duration').value;

        // Быстрая валидация
        if (!prompt) {
            showError('Пожалуйста, введите промпт');
            return;
        }
        if (!videoType) {
            showError('Пожалуйста, выберите тип видео');
            return;
        }

        // Скрываем предыдущие результаты и ошибки
        resultsDiv.style.display = 'none';
        errorDiv.style.display = 'none';
        storyboardSection.style.display = 'none';

        // Показываем загрузку
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline';

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
                    generate_storyboard: generateStoryboard,
                    video_type: videoType,
                    duration: parseInt(duration)
                })
            });

            const response = await Promise.race([fetchPromise, timeoutPromise]);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка сервера');
            }

            // Отображаем результаты
            scriptContent.textContent = data.script;
            resultsDiv.style.display = 'block';

            // Если есть раскадровка
            if (data.storyboard) {
                storyboardContent.textContent = data.storyboard;
                storyboardSection.style.display = 'block';
            }

        } catch (error) {
            showError(error.message);
        } finally {
            // Убираем загрузку
            submitBtn.disabled = false;
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    });

    function showError(message) {
        errorDiv.textContent = 'Ошибка: ' + message;
        errorDiv.style.display = 'block';
    }
});