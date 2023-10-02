from decouple import config
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Импорт категорий из вашего файла
from categories import categories

bot = telebot.TeleBot("5951286666:AAFN49EztoIhQn7Fh_Jsk2cUk-aV87yfOak")

total_budget = 0
user_categories = categories  # Используем категории из вашего файла
user_data = {}  # Добавляем словарь для хранения данных пользователя
common_expenses = []


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
    try:
        budget = int(message.text)
        total_budget = budget
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


def process_subcategory(message):
    user_data[message.chat.id]["subcategory"] = message.text  # Сохраняем выбранную подкатегорию в user_data
    if message.text == "Добавить деньги на бюджет":
        bot.send_message(message.chat.id, "Введите сумму для добавления на бюджет:")
        bot.register_next_step_handler(message, process_income)
    else:
        bot.send_message(message.chat.id, "Введите сумму расхода:")
        bot.register_next_step_handler(message, process_expense, user_data[message.chat.id]["subcategory"])


def counting_expenses(exp, categ):
    global common_expenses
    common_expenses.append({"category": categ, "expenses": exp})


def format_expenses():
    global common_expenses
    result_text = ""
    for item in common_expenses:
        result_text += ">>>" + item["category"] + ":    " + str(item["expenses"])+"!"
        result_text = result_text.replace("!", "\n")
    return result_text


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


def process_expense(message, *args):
    global total_budget
    subcategory = args[0]
    try:
        expense = int(message.text)
        print("process_expense message: ", message.text)
        print("process_expense subcateg: ", args[0])
        if expense > total_budget:
            bot.send_message(message.chat.id, f"Недостаточно средств для списания {expense} рублей.\n"
                                              f"На вашем счету :{total_budget}")
        else:
            total_budget -= expense
            counting_expenses(expense, subcategory)
            bot.send_message(message.chat.id, f"Списано {expense} рублей.\n"
                                              f"Остаток бюджета: {total_budget} рублей.\n"
                                              f"По категориям:\n{format_expenses()}")
        show_categories(message.chat.id)  # Позволяем пользователю выбрать следующую категорию
    except ValueError:
        bot.send_message(message.chat.id,
                         "Вы ввели неправильную сумму. Пожалуйста, введите сумму для списания цифрами.")


bot.polling()
