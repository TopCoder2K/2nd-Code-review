import telebot
import requests
import json
from app import bot
from decimal import *
from peewee import *


# Connect to database.
db = PostgresqlDatabase(database="postgres", user="postgres", password="TopCoder2000", host="localhost")


# Make a new table (if not exists).
class TgUser(Model):
    name = CharField()
    req_visits = IntegerField()
    cur_visits = IntegerField()
    user_id = IntegerField()

    class Meta:
        # Model will use "postgres.db".
        database = db


db.connect()
TgUser.create_table()


# A decorator to define command "/start" and make greetings.
@bot.message_handler(comands=["start"])
def start_message(message):
    bot.send_message(message.chat.id,
                     text="Hi, Im Jarvis. I can predict weather and count your physical education visiting.\n"
                          "If you want to start using the bot write '/help'.")


# A decorator to define command "/help" to help with registration.
@bot.message_handler(commands=["help"])
def handle_help(message):
    bot.send_message(message.chat.id, "To logon write '/reg'.\n"
                                      "To reset visits write '/new_semester'. (If you have already registered).")


# A decorator to define command "/reg" to start using the bot.
@bot.message_handler(commands=["reg"])
def handle_reg(message):
    flag = True
    try:
        TgUser.select().where(TgUser.user_id == message.chat.id).get()
    except DoesNotExist:
        flag = False
    if not flag:
        bot.send_message(message.chat.id, "What's your name?")
        bot.register_next_step_handler(message, get_name)
    else:
        user = TgUser.select().where(TgUser.user_id == message.chat.id).get()
        bot.send_message(message.chat.id, "Hi, {}!".format(user.name))
        weather_or_phys_edu(message)


# A decorator to define command "/new_semester" to reset physical education visits.
@bot.message_handler(commands=["new_semester"])
def handle_new_semester(message):
    flag = True
    user = None
    try:
        user = TgUser.select().where(TgUser.user_id == message.chat.id).get()
    except DoesNotExist:
        flag = False
    if flag:
        TgUser.update(cur_visits=0, req_visits=0).where(TgUser.user_id == message.chat.id).execute()
        bot.send_message(message.chat.id, "Ok, {}. I've just reset your physical education visits."
                         .format(user.name))
        weather_or_phys_edu(message)
    else:
        bot.send_message(message.chat.id, "You are not registred. Please, do it by command '/reg'.")


# Get interlocutor's name, save it and continue the registration. (+ later check unique names)
def get_name(message):
    user_name = message.text
    bot.send_message(message.chat.id, "Nice to meet you, {}. ".format(user_name))
    TgUser.create(name=user_name, req_visits=0, cur_visits=0, user_id=message.chat.id)
    weather_or_phys_edu(message)


# Determine the type of request.
def weather_or_phys_edu(message):
    # Our keyboard for answering.
    keyboard = telebot.types.InlineKeyboardMarkup()
    # "Yes" button.
    key_yes = telebot.types.InlineKeyboardButton(text="Yes", callback_data="yes, weather")
    keyboard.add(key_yes)
    # "No" button.
    key_no = telebot.types.InlineKeyboardButton(text="No", callback_data="no, sport")
    keyboard.add(key_no)
    bot.send_message(message.chat.id, "Would you like to know a weather forecast?", reply_markup=keyboard)


# Analyse the answer to request.
# If it's "yes", a period of time is needed.
@bot.callback_query_handler(func=lambda call: call.data == "yes, weather")
def callback_weather(call):
    bot.send_message(call.message.chat.id,
                     "So, in what city do you want to know the weather?")
    bot.register_next_step_handler(call.message, weather_json)


# If it's "no", initialise require number of visits and/or increase number of visits.
@bot.callback_query_handler(func=lambda call: call.data == "no, sport")
def callback_phys_edu(call):
    bot.send_message(call.message.chat.id,
                     "Then we will talk about your physical education visits.")
    user = TgUser.select().where(TgUser.user_id == call.message.chat.id).get()
    if user.req_visits == 0:
        bot.send_message(call.message.chat.id,
                         "How many times should you go to physical education per semester?")
        bot.register_next_step_handler(call.message, set_up_visits)
    else:
        add_visit(call.message)


# Initialise require number of visits
def set_up_visits(message):
    req_visits = 0
    # Check for adequate answer.
    try:
        req_visits = int(message.text)
    except (TypeError, ValueError):
        bot.send_message(message.chat.id, "Please, use numbers.")
        bot.register_next_step_handler(message, set_up_visits)

    # Check for correct answer.
    if req_visits > 1440:
        bot.send_message(message.chat.id,
                         "Hah. Are you from Exercise College?))) Your value are not allowed.\n"
                         "Write a correct number of visits.")
        bot.register_next_step_handler(message, set_up_visits)
    else:
        TgUser.update(req_visits=req_visits).where(TgUser.user_id == message.chat.id).execute()
        bot.send_message(message.chat.id, "Ok.")
        add_visit(message)


# Check if an interlocutor wants to add a physical education visit.
def add_visit(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    key_yes = telebot.types.InlineKeyboardButton(text="Yes", callback_data="yes, increase")
    keyboard.add(key_yes)
    key_no = telebot.types.InlineKeyboardButton(text="No", callback_data="no, don't touch")
    keyboard.add(key_no)
    bot.send_message(message.chat.id, "Would you like to score a physical education visit?",
                     reply_markup=keyboard)


# If it's "yes" increase cur_visits.
@bot.callback_query_handler(func=lambda call: call.data == "yes, increase")
def callback_weather(call):
    increase_visits(call.message)


# If it's "no", return to determining the type of request.
@bot.callback_query_handler(func=lambda call: call.data == "no, don't touch")
def callback_phys_edu(call):
    weather_or_phys_edu(call.message)


# Increase number of visits.
def increase_visits(message):
    user = TgUser.select().where(TgUser.user_id == message.chat.id).get()
    TgUser.update(cur_visits=user.cur_visits + 1).where(TgUser.user_id == message.chat.id).execute()
    # Number of visits are displayed.
    if user.req_visits + 1 == user.cur_visits:
        bot.send_message(message.chat.id,
                         "Now you have {} visits.\nOh, yeah! You did it!".format(user.cur_visits + 1))
    elif user.cur_visits + 1 >= user.req_visits / 2 \
            and user.cur_visits + 1 < user.req_visits:
        bot.send_message(message.chat.id,
                         "Now you have {} visits.\n"
                         "The half is behind. Don't slow down!".format(user.cur_visits + 1))
    else:
        bot.send_message(message.chat.id,
                         "Now you have {} visits.\nDamn! Rest in peace, bro.".format(user.cur_visits + 1))
    add_visit(message)


# Get the weather + city check.
def weather_json(message):
    # Open a page with the weather for a necessary city.
    city = message.text
    API_key = "f4188f71f275596f99e8e258020fa628"
    url = "http://api.openweathermap.org/data/2.5/weather?q={}&APPID={}".format(city, API_key)
    page = requests.get(url)
    API_call = json.loads(page.text)
    # Check that the city is found.
    if API_call["cod"] == 200:
        # Parse the json response.
        bot.send_message(message.chat.id, "Well, there what I've found about {}.".format(city))
        desc_list = API_call["weather"]
        bot.send_message(message.chat.id, "Weather description: {}".format(desc_list[0]["description"]))

        deviation = max(abs(API_call["main"]["temp_min"] - API_call["main"]["temp"]),
                        abs(API_call["main"]["temp_max"] - API_call["main"]["temp"]))

        getcontext().prec = 3
        temperature = Decimal(API_call["main"]["temp"]) - Decimal(273.0)
        deviation = Decimal(deviation) - Decimal(0.0)

        bot.send_message(message.chat.id, "Temperature: {} +- {} °C".format(temperature, deviation))

        getcontext().prec = 4
        pressure = Decimal(API_call["main"]["pressure"] * 0.750062) - Decimal(0.0)

        bot.send_message(message.chat.id, "Pressure: {} mm Hg".format(pressure))
        bot.send_message(message.chat.id, "Humidity: {} %".format(API_call["main"]["humidity"]))
        bot.send_message(message.chat.id,
                         "Wind speed: {} meter/sec. Wind degrees: {}°"
                         .format(API_call["wind"]["speed"], API_call["wind"]["deg"]))
        bot.send_message(message.chat.id, "Cloudiness: {}%".format(API_call["clouds"]["all"]))
        # bot.send_message(message.chat.id, "Rain for the last 3 hours: {} mm".format(API_call["rain"]["rain.3h"]))
        # bot.send_message(message.chat.id, "Snow for the last 3 hours: {} mm".format(API_call["snow"]["snow.3h"]))
        weather_or_phys_edu(message)
    else:
        bot.send_message(message.chat.id, "{} was not found, sorry. Try an another city =)".format(city))
        bot.register_next_step_handler(message, weather_json)
