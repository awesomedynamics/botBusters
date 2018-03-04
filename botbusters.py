import telebot
from telebot import types
from pymongo import MongoClient
import datetime
from flask import Flask, request
from flask_sslify import SSLify
import os
from mongo_api import update_booking, update_log, register_user

#подключаемся к монго
client = MongoClient(os.environ["MONGODB_URL"], username = os.environ["MONGODB_USERNAME"], password = os.environ["MONGODB_PASSWORD"], authSource = os.environ["MONGODB_AUTHSOURCE"])
db = client[os.environ["MONGODB_AUTHSOURCE"]]
bookings_coll = db.bookings
log_coll = db.log

no_keyboard = types.ReplyKeyboardRemove()

bot = telebot.TeleBot(os.environ["TOKEN"])
server = Flask(__name__)
sslify=SSLify(server)

#handling start or help command
@bot.message_handler(commands=['start','help'])
def start_command(message: telebot.types.Message):

    username = str(message.chat.first_name) + " " + str(message.chat.last_name)

    startText = "Привет!" + username + " Я - бот botBusters  \n  Хочешь, мы и тебе сделаем крутого чат-бота ? "
    bot.send_message(message.chat.id, startText)

    commands = ["Заказать бота", "А сайт у вас есть ?", "Сколько это стоит ?", "Перезвони мне"]

    markup = types.ReplyKeyboardMarkup(row_width=2,resize_keyboard=True)

    markup.row(commands[0],commands[1])
    markup.row(commands[2], commands[3])

    bot.send_message(message.chat.id, "что дальше ?",
                     reply_markup=markup)

    #Регистрируем юзера
    register_user(message)

# Обрабатываем кнопку "Заказать бота"
@bot.message_handler(func = lambda message: message.text is not None and message.text == "Заказать бота")
def order_bot(message: telebot.types.Message):
    reply_markup = types.ForceReply()
    bot.send_message(chat_id=message.chat.id, text="что должен делать бот:", reply_markup=reply_markup)


# Обрабатываем ответ о функционале бота
@bot.message_handler(func = lambda message: message.reply_to_message is not None and message.reply_to_message.text == "что должен делать бот:")
def bot_userstory(message: telebot.types.Message):
    update_booking(chat_id=message.chat.id, product="bot", userstory = message.text)
    reply_markup = types.ForceReply()
    bot.send_message(chat_id=message.chat.id, text="оставь нам свой телефон и мы перезвоним")
    bot.send_message(chat_id=message.chat.id, text="мой телефон:", reply_markup=reply_markup)

@bot.message_handler(func = lambda message: message.reply_to_message is not None and message.reply_to_message.text == "мой телефон:")
def  get_contact(message: telebot.types.Message):

    # апдейтим контакт в монго
    update_booking(chat_id=message.chat.id, contact=message.text)


    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons_final = ["В главное меню"]
    markup.row(buttons_final[0])


    bot.send_message(chat_id=message.chat.id, text="круто! мы перезвоним в ближайшее время !", reply_markup=markup)



#  обрабатываем кнопку Перезвони мне!

@bot.message_handler(func = lambda message: message.text is not None and message.text == "Перезвони мне")
def  book_callback(message: telebot.types.Message):
    reply_markup = types.ForceReply()
    bot.send_message(chat_id=message.chat.id, text="оставь нам свой телефон и мы перезвоним")
    bot.send_message(chat_id=message.chat.id, text="мой телефон:", reply_markup=reply_markup)


#  обрабатываем кнопку В главное меню
@bot.message_handler(func=lambda message: message.text is not None and message.text == "В главное меню")
def main_menu(message: telebot.types.Message):
    commands = ["Заказать бота", "А сайт у вас есть ?", "Сколько это стоит ?", "Перезвони мне"]

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    markup.row(commands[0], commands[1])
    markup.row(commands[2], commands[3])

    bot.send_message(message.chat.id, "что дальше ?",
                     reply_markup=markup)

#handling free text message
@bot.message_handler()
def free_text(message: telebot.types.Message):

    answer = "Я пока ничего об этом не знаю, но ты точно найдешь желанное на нашем сайте! "
    update_log(chat_id=message.chat.id, message=message)
    bot.send_message(message.chat.id, answer)


@server.route("/bot", methods=['POST','GET'])
def getMessage():
    if request.method == 'POST':
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!",200
    return '<h1>Hello bot</h1>'

@server.route("/")
def webhook():
     bot.remove_webhook()
     bot.set_webhook(url=os.environ["APP_URL"])
     return "!", 200