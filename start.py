# -*- coding: utf-8 -*-
import argparse
import app


def parse_args():
    parser = argparse.ArgumentParser(description="Simple telegram bot",
                                     formatter_class
                                     =argparse.ArgumentDefaultsHelpFormatter)
    #???
    parser.add_argument("--token-path", default="token")

    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.token_path, "r") as token_file:
        token = token_file.read()
    #???
    app.init_bot(token)
    app.bot.send_message(chat_id=665328452, text="YES")
    # Constantly checking for updates on the server.
    app.bot.polling(none_stop=True, interval=1)


if __name__ == "__main__":
    main()
