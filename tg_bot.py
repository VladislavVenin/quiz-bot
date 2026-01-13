import os
import random
from functools import partial

import redis
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from utils import get_questions_list


def format_answer(answer: str) -> str:
    answer = answer[:-1]
    clean_answer = ""
    for char in answer:
        if char == "(":
            break
        clean_answer += char
    clean_answer = clean_answer.lower()
    if clean_answer[-1] == " ":
        return clean_answer[:-1]
    return clean_answer


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        ["Новый вопрос", "Сдаться"],
        ["Мой счёт"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        'Здравствуйте! Я бот для викторин!',
        reply_markup=reply_markup
    )


def handle_buttons(update: Update, context: CallbackContext, database) -> None:
    """Handle menu buttons"""
    if update.message.text == "Новый вопрос":
        questions_folder = os.environ["QUESTIONS_FOLDER"]
        questions_file = "spb00per.txt"
        question = random.choice(get_questions_list(f"{questions_folder}/{questions_file}"))
        update.message.reply_text(question["question"])
        database.set(f"tg-{update.effective_chat.id}", question["answer"])
    else:
        answer = database.get(f"tg-{update.effective_chat.id}").decode('utf-8')
        user_answer = update.message.text
        if user_answer.lower() == format_answer(answer):
            positive_msg = "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»"
            update.message.reply_text(positive_msg)
        else:
            update.message.reply_text("Неправильно… Попробуешь ещё раз?")


def main() -> None:
    """Start the bot."""
    load_dotenv()
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    password = os.environ["DB_PASSWORD"]

    redis_db = redis.StrictRedis(host, port, password=password)
    handle_buttons_with_args = partial(handle_buttons, database=redis_db)

    token = os.environ["TG_TOKEN"]
    updater = Updater(token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_buttons_with_args))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
