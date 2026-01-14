import os
import random
from functools import partial

import redis
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
)

from utils import get_questions_list, format_answer


CHOOSING, ANSWERING = range(2)


def start(update: Update, context: CallbackContext):
    keyboard = [
        ["Новый вопрос", "Сдаться"],
        ["Мой счёт"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        'Здравствуйте! Я бот для викторин!',
        reply_markup=reply_markup
    )

    return CHOOSING


def handle_new_question_request(update: Update, context: CallbackContext, database):
    """Send a new question to the user and save the answer"""
    questions_folder = os.environ["QUESTIONS_FOLDER"]
    questions_file = random.choice(os.listdir(questions_folder))
    question = random.choice(get_questions_list(f"{questions_folder}/{questions_file}"))

    update.message.reply_text(question["question"])
    database.set(f"tg-{update.effective_chat.id}", question["answer"])

    return ANSWERING


def handle_solution_attempt(update: Update, context: CallbackContext, database):
    """Handle the attempt to give a solution"""
    user_key = f"tg-{update.effective_chat.id}"
    answer = database.get(user_key).decode('utf-8')
    user_answer = update.message.text
    if user_answer.lower() == format_answer(answer):
        positive_msg = "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»"
        update.message.reply_text(positive_msg)
        database.delete(user_key)
        return CHOOSING
    else:
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        return ANSWERING


def surrender(update: Update, context: CallbackContext, database):
    """Send the answer to the user and clear his note in DB"""
    user_key = f"tg-{update.effective_chat.id}"
    if database.get(user_key):
        answer = database.get(f"tg-{update.effective_chat.id}").decode('utf-8')
        update.message.reply_text(
            f"Очень жаль, ответ был: {answer}\nДля следующего вопроса нажми «Новый вопрос»"
        )
        database.delete(user_key)
    else:
        update.message.reply_text("Для следующего вопроса нажми «Новый вопрос»")
    return CHOOSING


def main() -> None:

    load_dotenv()
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    password = os.environ["DB_PASSWORD"]

    redis_db = redis.StrictRedis(host, port, password=password)
    question_requests = partial(handle_new_question_request, database=redis_db)
    solution_attempt = partial(handle_solution_attempt, database=redis_db)
    surrender_func = partial(surrender, database=redis_db)

    token = os.environ["TG_TOKEN"]
    updater = Updater(token)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(Filters.regex("^Новый вопрос$"), question_requests)],
            ANSWERING: [
                MessageHandler(Filters.regex("^Сдаться$"), surrender_func),
                MessageHandler(Filters.regex("^Новый вопрос$"), question_requests),
                MessageHandler(Filters.text, solution_attempt),
                ],
        },
        fallbacks=[MessageHandler(Filters.regex("^Сдаться$"), surrender_func)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
