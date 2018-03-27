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

    startText = "Привет " + username + " Я - BotMonster ! \n  Хочешь, мы и тебе сделаем крутого чат-бота ? "
    bot.send_message(message.chat.id, startText)

    main_menu(message)

    #Регистрируем юзера
    register_user(message)

# Обрабатываем кнопку "Заказать бота"
@bot.message_handler(func = lambda message: message.text is not None and message.text == "Заказать бота")
def order_bot(message: telebot.types.Message):
    reply_markup = types.ForceReply()
    bot.send_message(chat_id=message.chat.id, text="короткая пользовательская история:", reply_markup=reply_markup)


# Обрабатываем ответ о функционале бота
@bot.message_handler(func = lambda message: message.reply_to_message is not None and message.reply_to_message.text == "короткая пользовательская история:")
def bot_userstory(message: telebot.types.Message):
    update_booking(chat_id=message.chat.id, product="bot", userstory = message.text)
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    get_phone_button = types.KeyboardButton(text='Оставлю номер, позвоните', request_contact=True)
    markup.row(get_phone_button)
    bot.send_message(chat_id=message.chat.id, text="оставь нам свой телефон и мы перезвоним", reply_markup=markup)


#  обрабатываем кнопку В главное меню
@bot.message_handler(func=lambda message: message.text is not None and message.text == "В главное меню")
def main_menu(message: telebot.types.Message):
    commands = ["Заказать бота", "А сайт у вас есть ?", "Сколько это стоит ?", "Попробуй наших демо ботов"]

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    get_phone_button = types.KeyboardButton(text='Оставлю номер, позвоните', request_contact=True)

    markup.row(commands[0], commands[1])
    markup.row(commands[2], commands[3])
    markup.row(get_phone_button)

    bot.send_message(message.chat.id, "нажми на кнопку - получишь результат",
                     reply_markup=markup)



# saving the contact
@bot.message_handler(content_types= ["contact"])
def free_text(message: telebot.types.Message):

    answer = "это контакт, я понял! "
    update_log(chat_id=message.chat.id, message=message)
    bot.send_message(message.chat.id, answer)


#  handling free text message
@bot.message_handler()
def record_contact(message: telebot.types.Contact):

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