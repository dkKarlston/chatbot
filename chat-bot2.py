import re
import random
import webbrowser
import datetime
import requests
from urllib.parse import quote  # Импортируем quote для кодирования URL

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
    r"погода в (.+)": ["Получаю данные о погоде...", "Запрашиваю информацию о погоде...", "Сейчас узнаем погоду..."]
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

API_KEY = "5046b43bd8eb3af2655088b3d80132cc3"  # Замените на ваш API ключ


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
    try:
        # Кодируем название города для правильной передачи в URL
        city_encoded = quote(city)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_encoded}&appid={API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP-запроса
        data = response.json()

        # Получаем необходимые данные
        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        pressure = data["main"]["pressure"]
        # Получаем время восхода и заката (в формате timestamp)
        sunrise_timestamp = data["sys"]["sunrise"]
        sunset_timestamp = data["sys"]["sunset"]

        # Преобразуем timestamp в datetime объекты и форматируем их
        sunrise_time = datetime.datetime.fromtimestamp(sunrise_timestamp).strftime("%H:%M:%S")
        sunset_time = datetime.datetime.fromtimestamp(sunset_timestamp).strftime("%H:%M:%S")

        # Формируем ответ
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

    except requests.exceptions.RequestException as e:
        return f"Ошибка при запросе к API погоды: {e}"
    except (KeyError, TypeError) as e:
        return f"Не удалось получить информацию о погоде для города {city}. Ошибка в данных: {e}"


def chatbot_response(text):
    text = text.lower()
    response = None  # Initialize response to None

    # Проверка на арифметическое выражение
    match = re.search(r"(\d+(\.\d+)?\s*[\+\-\*/]\s*\d+(\.\d+)?)", text)
    if match:
        expression = match.group(1)
        return "Результат: " + calculate(expression)

    match = re.search(r"поиск\s+(.+)", text, re.IGNORECASE)
    if match:
        return search_web(match.group(1))

    # Проверяем запрос погоды
    match = re.search(r"погода в (.+)", text, re.IGNORECASE)
    if match:
        city = match.group(1)
        return get_weather(city)

    for pattern, reply in responses.items():
        if re.search(pattern, text):
            if isinstance(reply, list):
                response = random.choice(reply)
            elif callable(reply):
                response = reply()
            else:
                response = reply
            break  # если нашли соответствие, можно выходить из цикла, чтобы не искать дальше.

    if response is None:
        response = random.choice(["Я не понял вопрос.", "Попробуйте перефразировать.",
                                  "Пожалуйста, задайте вопрос по-другому."])

    return response


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
    chosen_category = None  # Инициализируем переменную для хранения выбранной категории

    while True:
        user_input = input("Вы: ")
        user_input_lower = user_input.lower()  # Переводим ввод в нижний регистр один раз

        if user_input_lower == "выход":
            print("Бот: До свидания!")
            break

        response = chatbot_response(user_input_lower)

        print("Бот:", response)  # Выводим ответ
        log_dialog(user_input, response)  # Логируем диалог

        if response == "О какой категории вы хотите узнать факт? (спорт, история, космос)":
            print("Бот:", response)
            category_input = input("Выберите категорию: ").lower()
            if category_input in facts:
                chosen_category = category_input
                fact = get_random_fact(chosen_category)
                print("Бот:", fact)
                chosen_category = None  # Сбрасываем категорию после вывода факта
            else:
                print("Бот: Нет фактов для этой категории.")
