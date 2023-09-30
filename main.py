from decouple import config
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from categories import categories

bot = telebot.TeleBot(config("TOKEN"))

total_budget = 0
total_budget2 = 0
user_categories = categories  # Используем категории из вашего файла
user_data = {}  # Добавляем словарь для хранения данных пользователя


@bot.message_handler(commands=["start", "testing"])
def get_hello(message):
    text = (f"Здравствуйте, {message.from_user.first_name} {message.from_user.username}!"
            f" Добро пожаловать!\n\n"
            f"Доступные команды:\n"
            f"/new_budget - установить новый бюджет\n")
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["new_budget"])
def ask_for_budget(message):
    markup = ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Введите ваш новый бюджет:", reply_markup=markup)
    bot.clear_step_handler(message)  # Сбрасываем предыдущий обработчик
    bot.register_next_step_handler(message, process_budget)


def process_budget(message):
    global total_budget
    global total_budget2
    try:
        budget = int(message.text)
        total_budget = budget
        total_budget2 = budget
        bot.send_message(message.chat.id, f"Ваш новый бюджет установлен: {total_budget}")
        user_data[message.chat.id] = {}  # Создаем пустой словарь для пользователя
        show_categories(message.chat.id)
    except ValueError:
        bot.send_message(message.chat.id, "Вы ввели неправильную сумму. Пожалуйста, введите сумму бюджета цифрами.")
        # Рекурсивно вызываем функцию для ввода бюджета снова
        bot.register_next_step_handler(message, process_budget)


def show_categories(chat_id):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    for category in user_categories:
        markup.add(KeyboardButton(category["name"]))
    bot.send_message(chat_id, "Выберите категорию:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_category)


def process_category(message):
    user_data[message.chat.id]["category"] = message.text  # Сохраняем выбранную категорию в user_data
    if message.text == "Добавить деньги на бюджет":
        bot.send_message(message.chat.id, "Введите сумму для добавления на бюджет:")
        bot.register_next_step_handler(message, process_income)
    elif message.text == "Посмотреть расходы":
        bot.send_message(message.chat.id, f"Общая сумма расхода состовляет: {total_budget2 - total_budget}")
        if total_budget == total_budget2:
            show_every_expenses()   # Нужно доработать функцию
        show_categories(message.chat.id)
    else:
        show_subcategories(message.chat.id, message.text)  # Показываем подкатегории


def show_subcategories(chat_id, category_name):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    category = next((cat for cat in user_categories if cat["name"] == category_name), None)
    if category:
        for subcategory in category["subcategories"]:
            markup.add(KeyboardButton(subcategory["name"]))
        bot.send_message(chat_id, "Выберите подкатегорию:", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, process_subcategory)
    else:
        bot.send_message(chat_id, "Что-то пошло не так. Пожалуйста, выберите категорию заново.")
        bot.register_next_step_handler_by_chat_id(chat_id, show_categories)


def process_subcategory(message):
    user_data[message.chat.id]["subcategory"] = message.text  # Сохраняем выбранную подкатегорию в user_data
    if message.text == "Добавить деньги на бюджет":
        bot.send_message(message.chat.id, "Введите сумму для добавления на бюджет:")
        bot.register_next_step_handler(message, process_income)
    else:
        bot.send_message(message.chat.id, "Введите сумму расхода:")
        bot.register_next_step_handler(message, process_expense)


def process_income(message):
    global total_budget
    try:
        income = int(message.text)
        total_budget += income
        bot.send_message(message.chat.id, f"Добавлено {income} рублей. Остаток бюджета: {total_budget} рублей.")
        show_categories(message.chat.id)  # Позволяем пользователю выбрать следующую категорию
    except ValueError:
        bot.send_message(message.chat.id,
                         "Вы ввели неправильную сумму. Пожалуйста, введите сумму для добавления на бюджет цифрами.")
        bot.register_next_step_handler(message, process_income)


def process_expense(message):
    global total_budget
    try:
        expense = int(message.text)
        if expense > total_budget:
            bot.send_message(message.chat.id, f"Недостаточно средств для списания {expense} рублей.\n"
                                              f"На вашем счету :{total_budget}")
        else:
            total_budget -= expense
            bot.send_message(message.chat.id, f"Списано {expense} рублей. Остаток бюджета: {total_budget} рублей.")
        show_categories(message.chat.id)  # Позволяем пользователю выбрать следующую категорию
    except ValueError:
        bot.send_message(message.chat.id,
                         "Вы ввели неправильную сумму. Пожалуйста, введите сумму для списания цифрами.")


def show_every_expenses():
    print()


bot.polling()
