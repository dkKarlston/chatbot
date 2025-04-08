import datetime
import os
import random
import re
import webbrowser
from urllib.parse import quote
import requests
import spacy
from textblob import TextBlob
from googletrans import Translator


# Загрузка spaCy модели для русского языка
try:
    nlp = spacy.load("ru_core_news_sm")
except OSError:
    print("Модель ru_core_news_sm не найдена. Загружаю...")
    import spacy.cli

    spacy.cli.download("ru_core_news_sm")
    nlp = spacy.load("ru_core_news_sm")

# Определяем словарь шаблонов и ответов
responses = {
    r"как тебя зовут\??": ["Я бот-помощник!", "Меня зовут Бот.", "Я - ваш виртуальный ассистент."],
    r"как дела\??": ["Спасибо, у меня всё хорошо!",
                     "Неплохо, а у тебя?",
                     "Я просто программа, но чувствую себя отлично!"],
    r"что ты умеешь\??": ["Я умею отвечать на вопросы, искать информацию и выполнять команды!",
                          "Мои возможности ограничены, но я могу помочь с простыми задачами.",
                          "Я могу помочь вам найти информацию в интернете или рассказать что-нибудь интересное."],
    r"сколько сейчас время\??": lambda: datetime.datetime.now().strftime("Сейчас время %H:%M:%S"),
    r"какое сегодня число\??": lambda: datetime.date.today().strftime("Сегодня %d.%m.%Y"),
    r"расскажи интересный факт": ["О какой категории вы хотите узнать факт? (спорт, история, космос)",
                                  "Я могу рассказать факт о спорте, истории или космосе. Что вас интересует?"],
    r"еще один факт": ["О какой категории вы хотите узнать факт? (спорт, история, космос)",
                       "Из какой области вы хотите узнать новый факт?"],
    r"поиск\s(.+)": ["Ищу в интернете...", "Начинаю поиск в Google...", "Сейчас найду это в сети..."],
    r"погода в (.+)": ["Получаю данные о погоде...", "Запрашиваю информацию о погоде...", "Сейчас узнаем погоду..."],
    r"\bпривет\b": [
        "Привет-привет! 😊 Как твои дела?",
        "Здравствуйте! Чем могу помочь сегодня?",
        "Йо! Рад тебя видеть!",
    ],
    r"\bнастоящий\b|\bживой\b|\bчеловек\b": [
        "Я пока не человек... но уже с характером! 😏",
        "Почти! Только не пью чай и не хожу в магазин 😄",
    ],
    r"\bспасибо\b|\bблагодарить\b": [
        "Рад помочь! Обращайся в любое время 😊",
        "Всегда пожалуйста! Чем ещё могу быть полезен?",
        "Пожалуйста!",
    ],
    r"\bпока\b|\bсвидание\b": [
        "До встречи! Надеюсь, скоро снова поболтаем 👋",
        "Пока! Береги себя!",
    ],
    r"\bдело\b|\bновый\b": [
        "Всё в порядке, спасибо, что спросил!",
        "Чудесно!",
    ],
    r"\bуметь\b": [
        "Я умею отвечать на вопросы, считать несложные выражения. Могу найти всё, что тебе нужно!",
    ],

    r"\bвремя\b|\bчас\b": lambda _: datetime.datetime.now().strftime("Сейчас %H:%M."),
    r"\bчисло\b|\bдата\b": lambda _: datetime.date.today().strftime("Сегодня %d.%m.%Y"),
    r"\bнайди\b\s+(.+)": lambda m: search_web(m.group(1)),
}

# Словарь фактов по категориям
facts = {
    "спорт": [
        "Бадминтон – является самым быстрым ракеточным видом спорта: скорость полета волана может достигать в среднем "
        "270 км/час.",
        "В стандартном мячике для гольфа всего 336 выемок.",
        "В пелотоне Формулы-1 нет болида под номером 13, после 12-го сразу идёт 1",
        "Фернандо Алонсо, гонщик «Формулы-1», сел за руль карта в три года.",
        "Нильс Бор, знаменитый физик, был вратарём сборной Дании.",
    ],
    "история": [
        "Великая китайская стена не видна с Луны невооруженным глазом.",
        "Первая фотография была сделана в 1826 году.",
        "Рим был основан в 753 году до нашей эры.",
        "Петр».",
        "Арабские цифры изобрелись не арабами, а математиками из Индии.",
        "Когда-то морфин использовался для уменьшения кашля.",
    ],
    "космос": [
        "Температура на поверхности Венеры достигает 465°C, что горячее, чем на Меркурии, хотя Венера дальше от Солнца.",
        "Самая высокая гора в Солнечной системе - гора Олимп на Марсе. Ее высота достигает 21 километр.",
        "Нейтронные звезды могут вращаться со скоростью до 600 оборотов в секунду.",
        "В космосе нельзя заплакать. В условиях микрогравитации слезы не падают вниз, как на Земле, а остаются на "
        "глазах в виде маленьких капель.",
        "В космосе нет звука. Звук не может распространяться в вакууме, так как ему нужны молекулы воздуха или "
        "другого вещества для передачи волн.",
        "Сатурн может плавать в воде. Если бы существовал бассейн с водой достаточного размера, Сатурн, из-за своей "
        "низкой плотности, плавал бы на поверхности.",
    ],
}

API_KEY = "c4aec831b9f8a6d4a4acc553848b76ff"


class ActionGetWeather:
    def __init__(self):
        self.api_key = API_KEY

    def name(self):
        return "action_get_weather"

    def run(self, city):
        try:
            city_encoded = quote(city)
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city_encoded}&appid={self.api_key}&units=metric&lang=ru"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            temp = data["main"]["temp"]
            weather_desc = data["weather"][0]["description"]
            pressure = data["main"]["pressure"]
            sunrise_timestamp = data["sys"]["sunrise"]
            sunset_timestamp = data["sys"]["sunset"]

            sunrise_time = datetime.datetime.fromtimestamp(sunrise_timestamp).strftime("%H:%M:%S")
            sunset_time = datetime.datetime.fromtimestamp(sunset_timestamp).strftime("%H:%M:%S")

            weather_responses = [
                (f"В городе {city} сейчас {weather_desc}, температура {temp}°C, "
                 f"атмосферное давление {pressure} гПа.\n"
                 f"Время восхода: {sunrise_time}, время заката: {sunset_time}"),
                (f"Погода в {city}: {weather_desc}, {temp}°C, давление {pressure} гПа. "
                 f"Восход в {sunrise_time}, закат в {sunset_time}."),
                (f"Сейчас в {city} {weather_desc}, температура воздуха {temp} градусов Цельсия, "
                 f"давление {pressure} гектопаскалей. Солнце встало в {sunrise_time}, а сядет в {sunset_time}.")
            ]
            return random.choice(weather_responses)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return "Город не найден. Пожалуйста, уточните название города."
            else:
                return "Произошла ошибка при получении данных о погоде."
        except Exception as e:
            return f"Произошла ошибка: {e}"


def process_text(text):
    doc = nlp(text)
    return [token.lemma_ for token in doc if not token.is_punct and not token.is_space]


def calculate(expression):
    try:
        expression = expression.replace('x', '*')
        result = eval(expression)
        return str(result)
    except (SyntaxError, TypeError, NameError, ZeroDivisionError):
        return "Не могу вычислить это выражение."


def get_random_fact(category):
    if category in facts:
        return random.choice(facts[category])
    else:
        return "Нет фактов для этой категории."


def search_web(query):
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open_new_tab(url)
        return random.choice([f"Открываю Google с запросом: {query}", f"Ищу '{query}' в Google..."])
    except webbrowser.Error:
        return "Не удалось открыть браузер. Пожалуйста, убедитесь, что у вас установлен браузер по умолчанию."


def log_dialog(user_input, bot_response):
    with open("chat_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"Пользователь: {user_input}\n")
        log_file.write(f"Бот: {bot_response}\n")
        log_file.write("-" * 40 + "\n")


def get_weather(city):
    weather_action = ActionGetWeather()
    return weather_action.run(city)


def lemmatize_text(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])


def analyze_sentiment(text):
    try:
        # Сначала попробуем проанализировать русский текст напрямую
        russian_sentiment = TextBlob(text).sentiment.polarity

        # Если анализ на русском дал нейтральный результат, попробуем перевод
        if -0.3 <= russian_sentiment <= 0.3:
            translator = Translator()
            translated = translator.translate(text, src='ru', dest='en').text
            english_sentiment = TextBlob(translated).sentiment.polarity
            polarity_score = english_sentiment
        else:
            polarity_score = russian_sentiment

        if polarity_score > 0.3:
            return "Ты звучишь очень позитивно! 😄 Чем могу порадовать тебя ещё?"
        elif polarity_score < -0.3:
            return "Ты, похоже, не в настроении... 😔 Хочешь поговорить об этом?"
        else:
            return "Улавливаю нейтральный настрой. Спрашивай, если что-нибудь нужно!"
    except Exception as e:
        print(f"Ошибка при анализе настроения: {e}")
        return "Хм... сложно понять твоё настроение. Но я здесь, если что 😊"


def chatbot_response(user_input, chosen_category=None):
    user_input_lower = user_input.lower()

    if chosen_category:
        if user_input_lower in facts:
            return get_random_fact(user_input_lower)
        else:
            return "Нет фактов для этой категории."

    # Проверка на запрос факта
    if re.search(r"расскажи интересный факт", user_input_lower):
        return "О какой категории вы хотите узнать факт? (спорт, история, космос)"

    # Проверка на арифметическое выражение
    match = re.search(r"(\d+(\.\d+)?\s*[\+\-\*/]\s*\d+(\.\d+)?)", user_input_lower)
    if match:
        expression = match.group(1)
        return "Результат: " + calculate(expression)

    match = re.search(r"поиск\s+(.+)", user_input_lower, re.IGNORECASE)
    if match:
        return search_web(match.group(1))

    match = re.search(r"погода в (.+)", user_input_lower, re.IGNORECASE)
    if match:
        city = match.group(1)
        return get_weather(city)

    for pattern, reply in responses.items():
        if re.search(pattern, user_input_lower):
            if isinstance(reply, list):
                return random.choice(reply)
            elif callable(reply):
                return reply()
            else:
                return reply

    # Если ни одно условие не выполнено, возвращаем ответ на основе тональности
    return analyze_sentiment(user_input)


if __name__ == "__main__":
    print("Привет! Вы можете задать мне следующие запросы:\n"
          "- Как тебя зовут?\n"
          "- Что ты умеешь?\n"
          "- Сколько сейчас время?\n"
          "- Какое сегодня число?\n"
          "- Какая сейчас погода?\n"
          "- Расскажи интересный факт\n"
          "- Вычисления (например, 2 + 2)\n"
          "- Поиск в интернете (например, 'поиск котики')\n"
          "- Погода в [город] (например, 'Погода в Москве')\n"
          "- Введите 'выход' для завершения диалога.\n"
          "Чем могу быть полезен?")

    chosen_category = None

    if not os.path.exists("chat_log.txt"):
        with open("chat_log.txt", "w", encoding="utf-8") as f:
            f.write("Начало диалога\n")

    while True:
        user_input = input("Вы: ")
        user_input_lower = user_input.lower()

        if user_input_lower == "выход":
            print("Бот: До свидания!")
            break

        if chosen_category:
            response = chatbot_response(user_input, chosen_category)
            chosen_category = None
        else:
            response = chatbot_response(user_input)
            if response == "О какой категории вы хотите узнать факт? (спорт, история, космос)":
                chosen_category = True

        print("Бот:", response)
        log_dialog(user_input, response)