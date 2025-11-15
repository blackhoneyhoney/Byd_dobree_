from flask import Flask, render_template, request, jsonify
import os
import time
from dotenv import load_dotenv
import logging
import openai
import httpx

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные из .env
load_dotenv()

# API ключ - ДОЛЖЕН БЫТЬ ДЕЙСТВИТЕЛЬНЫМ
TOKEN = os.getenv("GEMINI_API_KEY")

# Настройка клиента с прокси
# Конфигурация прокси
proxy_config = "http://MKnEA2:hgbt68@168.81.65.13:8000"

try:
    # Новый синтаксис для httpx
    proxies = {
        "http://": proxy_config,
        "https://": proxy_config
    }
    client = httpx.Client(
        proxies=proxies,
        timeout=30.0,
    )
    logger.info("✅ Прокси настроен")
except Exception as e:
    logger.warning(f"⚠️ Ошибка настройки прокси: {e}. Работа без прокси.")
    client = httpx.Client(timeout=30.0)

openai_client = openai.OpenAI(
    http_client=client,
    api_key=TOKEN,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

app = Flask(__name__)


def generate_with_gemini(prompt, max_retries=3):
    """Универсальная функция генерации с повторными попытками"""

    for attempt in range(max_retries):
        try:
            logger.info(f"🤖 Попытка генерации {attempt + 1}")

            response = openai_client.chat.completions.create(
                model="gemini-2.0-flash-lite",  # Используем Flash-Lite модель
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=2048,
                timeout=30
            )

            content = response.choices[0].message.content
            if content and content.strip():
                return content
            else:
                raise Exception("Пустой ответ от API")

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"⚠️ Ошибка (попытка {attempt + 1}): {error_msg}")

            if attempt == max_retries - 1:
                raise e

            # Увеличиваем задержку между попытками
            time.sleep(2 * (attempt + 1))


def generate_script(prompt, video_type, duration):
    """Генерация детального сценария"""
    duration_text = f"{duration} секунд"
    if duration >= 60:
        minutes = duration // 60
        duration_text = f"{minutes} минут"

    system_prompt = f"""Ты профессиональный сценарист для социальных сетей. Создай детальный сценарий для {video_type} рилса длительностью {duration_text}.

ТЕМА: {prompt}

Формат:
1. КОНЦЕПЦИЯ: [идея видео]
2. СЦЕНЫ (4-6 сцен с временными метками):
- [0-5с] [описание сцены] | [визуал] | [звук] | [эмоция]
- [6-12с] [описание сцены] | [визуал] | [звук] | [эмоция]
- [13-20с] [описание сцены] | [визуал] | [звук] | [эмоция]
- [21-30с] [описание сцены] | [визуал] | [звук] | [эмоция]
3. ПРИЗЫВ К ДЕЙСТВИЮ: [текст]

Сделай сценарий виральным и эмоциональным."""

    try:
        logger.info(f"Начало генерации сценария: {prompt[:50]}...")
        start_time = time.time()

        script = generate_with_gemini(system_prompt)

        elapsed = time.time() - start_time
        logger.info(f"✅ Сценарий получен за {elapsed:.1f} сек")

        return script

    except Exception as e:
        raise Exception(f"Ошибка при генерации сценария: {str(e)}")


def generate_storyboard(prompt, script, video_type, duration):
    """Генерация детальной раскадровки"""
    duration_text = f"{duration} секунд"
    if duration >= 60:
        minutes = duration // 60
        duration_text = f"{minutes} минут"

    # Обрезаем слишком длинный скрипт
    truncated_script = script[:1000] + "..." if len(script) > 1000 else script

    system_prompt = f"""Создай раскадровку для {video_type} видео длительностью {duration_text} на тему "{prompt}".

ОСНОВНОЙ СЦЕНАРИЙ:
{truncated_script}

Формат для 4-6 сцен:
СЦЕНА [номер] ([время]):
• Кадр: [композиция и визуал]
• Действие: [что происходит]
• Эмоция: [какую эмоцию вызывает]"""

    try:
        logger.info("🎨 Генерация раскадровки...")
        start_time = time.time()

        storyboard = generate_with_gemini(system_prompt)

        elapsed = time.time() - start_time
        logger.info(f"✅ Раскадровка получена за {elapsed:.1f} сек")

        return storyboard

    except Exception as e:
        raise Exception(f"Ошибка при генерации раскадровки: {str(e)}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health_check():
    """Эндпоинт для проверки здоровья API"""
    try:
        if not TOKEN:
            return jsonify({"status": "error", "message": "API ключ не настроен"}), 500

        # Быстрая проверка
        response = openai_client.chat.completions.create(
            model="gemini-2.0-flash-lite",
            messages=[{"role": "user", "content": "Тест"}],
            max_tokens=5,
            timeout=10
        )

        return jsonify({
            "status": "healthy",
            "gemini": "working",
            "model": "gemini-2.0-flash-lite",
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "gemini": "not_working"
        }), 500


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        prompt = data.get("prompt", "").strip()
        generate_storyboard_flag = data.get("generate_storyboard", False)
        video_type = data.get("video_type", "развлекательного")
        duration = min(int(data.get("duration", 30)), 60)

        # Валидация
        if not prompt:
            return jsonify({"error": "Введите промпт"}), 400

        if len(prompt) > 500:
            return jsonify({"error": "Слишком длинный промпт. Максимум 500 символов."}), 400

        if not TOKEN:
            return jsonify({"error": "Не настроен API ключ Gemini. Создайте файл .env с GEMINI_API_KEY"}), 500

        logger.info(f"Запрос генерации: {prompt[:50]}...")

        # Генерируем сценарий
        script = generate_script(prompt, video_type, duration)

        result = {
            "script": script,
            "storyboard": None
        }

        # Генерация раскадровки если нужно
        if generate_storyboard_flag:
            storyboard = generate_storyboard(prompt, script, video_type, duration)
            result["storyboard"] = storyboard

        logger.info("✅ Генерация завершена успешно!")
        return jsonify(result)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Ошибка генерации: {error_msg}")

        # Более понятные сообщения об ошибках
        if "API ключ" in error_msg or "TOKEN" in error_msg:
            error_msg = "Не настроен API ключ Gemini. Создайте файл .env с GEMINI_API_KEY"
        elif "quota" in error_msg.lower():
            error_msg = "Превышена дневная квота Gemini API. Попробуйте завтра или используйте другой API ключ."
        elif "429" in error_msg:
            error_msg = "Слишком много запросов. Подождите немного."
        elif "503" in error_msg or "Service Unavailable" in error_msg:
            error_msg = "Сервер Gemini временно недоступен. Попробуйте позже."
        elif "401" in error_msg:
            error_msg = "Неверный API ключ Gemini. Проверьте ключ в .env"
        elif "timeout" in error_msg.lower() or "Timeout" in error_msg:
            error_msg = "Превышено время ожидания ответа. Попробуйте еще раз."
        elif "404" in error_msg:
            error_msg = "Модель gemini-2.0-flash-lite не найдена. Проверьте доступность модели."
        elif "proxy" in error_msg.lower():
            error_msg = "Ошибка подключения через прокси. Проверьте настройки прокси."

        return jsonify({"error": error_msg}), 500


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Внутренняя ошибка сервера: {error}")
    return jsonify({"error": "Внутренняя ошибка сервера"}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Эндпоинт не найден"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
