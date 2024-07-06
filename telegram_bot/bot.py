import telebot
import requests
from secret import API_TOKEN
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_URL = 'http://parse_project_backend:8000'

bot = telebot.TeleBot(API_TOKEN)

user_data = {}


def get_buttons_filters():
    keyboard = InlineKeyboardMarkup()
    filters = ["Название вакансии", "Мин. зарплата", "Макс. зарплата", "Тип занятости", "Опыт работы", "Работодатель",
               "Город"]
    callbacks = ["name", "salary_min", "salary_max", "employment", "experience", "employer", "city"]

    for i in range(0, len(filters), 2):
        row = [InlineKeyboardButton(filters[i], callback_data=f"{callbacks[i]}")]
        if i + 1 < len(filters):
            row.append(InlineKeyboardButton(filters[i + 1], callback_data=f"{callbacks[i + 1]}"))
        keyboard.row(*row)

    keyboard.row(InlineKeyboardButton("Начать поиск", callback_data="search"))
    return keyboard


@bot.message_handler(commands=['start', 'filter'])
def send_filter_options(message):
    user_data[message.chat.id] = {
        'name': None,
        'salary_from': None,
        'salary_to': None,
        'employment_status': None,
        'work_experience': None,
        'employer': None,
        'city': None,
    }
    bot.send_message(message.chat.id, "Выберите критерии, по которым хотите отфильтровать вакансии:",
                     reply_markup=get_buttons_filters())


@bot.callback_query_handler(func=lambda call: call.data in ["name", "salary_min", "salary_max", "employment", "experience", "employer", "city"])
def filter_callback(call):
    msg = f"Укажите значение для параметра '{call.data}':"
    bot.send_message(call.message.chat.id, msg)
    bot.register_next_step_handler(call.message, set_filter_value, call.data)


def set_filter_value(message, param):
    user_data[message.chat.id][param] = message.text
    bot.send_message(message.chat.id, f"Значение параметра '{param}' установлено на '{message.text}'",
                     reply_markup=get_buttons_filters())


@bot.callback_query_handler(func=lambda call: call.data == 'search')
def search_vacancies(call):
    params = user_data.get(call.message.chat.id, {})
    params = {k: v for k, v in params.items() if v}

    try:
        response = requests.get(f"{API_URL}/vacancy", params=params)
        response.raise_for_status()
        vacancies = response.json()
    except requests.exceptions.RequestException as e:
        bot.send_message(call.message.chat.id, f"Ошибка при запросе к API: {e}")
        return
    except ValueError:
        bot.send_message(call.message.chat.id,
                         f"Ошибка при декодировании ответа API. Содержимое ответа:\n{response.text}")
        return

    if not vacancies:
        bot.send_message(call.message.chat.id, "Вакансии не найдены.")
        return

    for vacancy in vacancies:
        try:
            msg = (f"{vacancy.get('name')} \n"
                   f"{vacancy.get('employment_status')}"
                   f"\n {vacancy.get('work_experience')}")
            msg += (f"\n от {vacancy.get('salary_from')}" if vacancy.get('salary_from') else "") + \
                   (f" до {vacancy.get('salary_to')}" if vacancy.get('salary_to') else "") + \
                   (f" {vacancy.get('currency')}" if vacancy.get('currency') else "")

            if vacancy.get("city"):
                msg += f"\n г. {vacancy.get('city')}"
            msg += f"\n Работодатель: {vacancy.get('employer')}"
            msg += f"\n {vacancy.get('address') if vacancy.get('address') else ''}"
            bot.send_message(call.message.chat.id, msg)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Ошибка при обработке данных вакансии: {str(e)}")


if __name__ == "__main__":
    bot.polling(none_stop=True)
