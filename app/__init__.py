import telebot

bot = None

NAME = ''
REQ_VISITS = 0
CUR_VISITS = 0


def init_bot(token):
    global bot
    bot = telebot.TeleBot(token)

    from app import TelegramBot
