import random
import os

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import vk_api as vk
from dotenv import load_dotenv
import redis

from utils import get_questions_list, format_answer


def send_message(event, vk_api, message):
    vk_api.messages.send(
            user_id=event.user_id,
            message=message,
            random_id=random.randint(1, 1000),
        )


def start(event, vk_api, keyboard):
    vk_api.messages.send(
            user_id=event.user_id,
            message="Здравствуйте! Я бот для викторин!",
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )


def handle_new_question_request(event, vk_api, database):
    """Send a new question to the user and save the answer"""
    questions_folder = os.environ["QUESTIONS_FOLDER"]
    questions_file = random.choice(os.listdir(questions_folder))
    question = random.choice(get_questions_list(f"{questions_folder}/{questions_file}"))

    send_message(event, vk_api, question["question"])
    database.set(f"vk-{event.user_id}", question["answer"])


def surrend(event, vk_api, database):
    """Send the answer to the user and clear his note in DB"""
    user_key = f"vk-{event.user_id}"
    if database.get(user_key):
        answer = database.get(user_key).decode('utf-8')
        message = f"Очень жаль, ответ был: {answer}\nДля следующего вопроса нажми «Новый вопрос»"
        send_message(event, vk_api, message)
        database.delete(user_key)
    else:
        message = "Для следующего вопроса нажми «Новый вопрос»"
        send_message(event, vk_api, message)


def handle_solution_attempt(event, vk_api, database):
    """Handle attempt to give solution"""
    user_key = f"vk-{event.user_id}"
    answer = database.get(user_key).decode('utf-8')
    user_answer = event.text

    if user_answer.lower() == format_answer(answer):
        message = "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»"
        send_message(event, vk_api, message)
        database.delete(user_key)
    else:
        message = "Неправильно… Попробуешь ещё раз?"
        send_message(event, vk_api, message)


def main():
    load_dotenv()
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    password = os.environ["DB_PASSWORD"]
    redis_db = redis.StrictRedis(host, port, password=password)

    token = os.environ["VK_TOKEN"]
    vk_session = vk.VkApi(token=token)
    vk_api = vk_session.get_api()

    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.SECONDARY)

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "Начать":
                start(event, vk_api, keyboard)
            elif event.text == "Сдаться":
                surrend(event, vk_api, redis_db)
            elif event.text == "Новый вопрос":
                handle_new_question_request(event, vk_api, redis_db)
            elif event.text == "Мой счёт":
                message = "Этой функции ещё нет...",
                send_message(event, vk_api, message)
            else:
                if redis_db.get(f"vk-{event.user_id}"):
                    handle_solution_attempt(event, vk_api, redis_db)


if __name__ == '__main__':
    main()
