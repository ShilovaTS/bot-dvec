# This is a sample Python script.
from telebot import telebot, types
from random import randint
import parse

# сохраняем шаги
states = {}
inventories = {}

# Создаем экземпляр бота

bot = telebot.TeleBot('5194194605:AAE520RKe5T2cvkl0TVTmDSTSp0zqrmqAeM')


# Функция, обрабатывающая команду /start

@bot.message_handler(commands=["start"])
def start(m, res=False):
    user = m.chat.id

    states[user] = 0
    inventories[user] = []

    bot.send_message(user, "Добро пожаловать в ...! Здесь вы можете передать показания по электрической энергии. ")
    process_state(user, states[user], inventories[user])

    # Получение сообщений от юзера


@bot.message_handler(content_types=["text"])
def handle_text(message):
    user = message.chat.id
    try:
        if states[user] == 0:
            wr = message.text.split("/")
            req = {
                "account": wr[0],
                "meter": wr[1],
                "branch": 'aes',
                "step": '1'
            }
            inventories[user] = parse.get_info(req)
            print(req["step"], inventories[user]["step"])
            if (req["step"] != inventories[user]["step"]):
                states[user] = 1
            else:
                bot.send_message(message.chat.id, inventories[user]["alert"])

        if states[user] == 2:
            req = {
                "reading1": message.text,
                "branch": 'aes',
                "step": '2',
                "sessionkey": inventories[user]['sessionkey']
            }
            inventories[user] = parse.get_info(req)
            states[user] = 3

        bot.send_message(message.chat.id, inventories[user]['answ'])
        process_state(user, states[user], inventories[user])

    except Exception as ex:
        bot.send_message(message.chat.id, inventories[user]['alert'])


@bot.callback_query_handler(func=lambda call: True)
def user_answer(call):
    user = call.message.chat.id
    process_answer(user, call.data)


def process_state(user, state, inventory):
    kb = types.InlineKeyboardMarkup()

    if state == 0:
        bot.send_message(user,
                         "Введите номер лицевого счета и номер прибора учета через /. Например: 012044743/14027470")

    if state == 1:
        kb.add(types.InlineKeyboardButton(text="Да", callback_data="1"))
        kb.add(types.InlineKeyboardButton(text="Нет", callback_data="2"))

        bot.send_message(user, "Все верно?",
                         reply_markup=kb)

    if state == 3:
        kb.add(types.InlineKeyboardButton(text="Подтвердить", callback_data="1"))
        kb.add(types.InlineKeyboardButton(text="Назад", callback_data="2"))

        bot.send_message(user, "Пожалуйста, проверьте введенные данные. "
                               "Если данные верны, подтвердите их отправку с помощью кнопки Подтвердить.",
                         reply_markup=kb)


def process_answer(user, answer):
    if states[user] == 1:
        if answer == "2":
            bot.send_message(user,
                             "Проверьте правильность набора лицевого счета или номера прибора")
            states[user] = 0
        else:
            bot.send_message(user, "Введите текущие показания прибора учета")
            states[user] = 2

    if states[user] == 3:
        if answer == "2":
            bot.send_message(user, "Введите корректные текущие показания прибора учета")
            states[user] = 2
        else:
            req = {
                "reading1": inventories[user]['reading1'],
                "branch": 'aes',
                "step": '3',
                "sessionkey": inventories[user]['sessionkey']
            }
            msg = parse.set_reading(req)
            states[user] = 4
            bot.send_message(user, "Ваши показания приняты")

    process_state(user, states[user], inventories[user])

    # Запускаем бота


bot.polling(none_stop=True, interval=0)
