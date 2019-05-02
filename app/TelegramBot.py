import telebot
import requests
import json
import database
from app import bot, NAME, REQ_VISITS, CUR_VISITS
from decimal import *


# A decorator to define command "/start" and make greetings.
@bot.message_handler(comands=["start"])
def start_message(message):
    bot.send_message(message.chat.id,
                     text="Hi, Im Jarvis. I can predict weather and count your physical education visiting."
                          "If you want to start using the bot write '/help'.")


# A decorator to define command "/help" to help with registration.
@bot.message_handler(commands=["help"])
def handle_help(message):
    bot.send_message(message.chat.id, "To logon write '/reg'.\n"
                                      "To reset visits write '/new_semester'.")


# A decorator to define command "/reg" to start using the bot.
@bot.message_handler(commands=["reg"])
def handle_reg(message):
    bot.send_message(message.chat.id, "What's your name?")
    bot.register_next_step_handler(message, get_name)


# A decorator to define command "/new_semester" to reset physical education visits.
@bot.message_handler(commands=["new_semester"])
def handle_reg(message):
    global CUR_VISITS, REQ_VISITS
    CUR_VISITS = 0
    REQ_VISITS = 0
    bot.send_message(message.chat.id, "Ok. You reset your physical education visits.")
    weather_or_phys_edu(message)


# Get interlocutor's name, save it and continue the registration. (+ later check unique names)
def get_name(message):
    global NAME
    NAME = message.text
    bot.send_message(message.chat.id, "Nice to meet you, {}. ".format(NAME))
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
    if REQ_VISITS == 0:
        bot.send_message(call.message.chat.id,
                         "How many times should you go to physical education per semester?")
        bot.register_next_step_handler(call.message, set_up_visits)
    else:
        add_visit(call.message)


# Initialise require number of visits
def set_up_visits(message):
    global REQ_VISITS
    # Check for adequate answer.
    try:
        REQ_VISITS = int(message.text)
    except (TypeError, ValueError):
        bot.send_message(message.chat.id, "Please, use numbers.")
        bot.register_next_step_handler(message, set_up_visits)

    # Check for correct answer.
    if REQ_VISITS > 1440:
        bot.send_message(message.chat.id,
                         "Hah. Are you from Exercise College?))) Your value are not allowed.\n"
                         "Write a correct number of visits.")
        bot.register_next_step_handler(message, set_up_visits)
    else:
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
    global CUR_VISITS
    CUR_VISITS = CUR_VISITS + 1
    # Number of visits are displayed.
    if CUR_VISITS == REQ_VISITS:
        bot.send_message(message.chat.id,
                         "Now you have {} visits.\nOh, yeah! You did it!".format(CUR_VISITS))
    elif CUR_VISITS >= REQ_VISITS / 2 and CUR_VISITS < REQ_VISITS:
        bot.send_message(message.chat.id,
                         "Now you have {} visits.\n"
                         "The half is behind. Don't slow down!".format(CUR_VISITS))
    else:
        bot.send_message(message.chat.id, "Now you have {} visits.\nDamn! Rest in peace, bro.".format(CUR_VISITS))
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
        bot.send_message(message.chat.id, "Well, {}. There what I've found about {}.".format(NAME, city))
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
