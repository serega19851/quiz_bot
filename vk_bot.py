# -*- coding: utf-8 -*-
import argparse
import difflib
import logging
import os
import random
from time import sleep

import redis
import vk_api
from environs import Env
from redis.commands.json.path import Path
from requests.exceptions import ConnectionError
from vk_api.keyboard import VkKeyboard
from vk_api.keyboard import VkKeyboardColor
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll

from questions_answers import gets_random_questions_answers

logger = logging.getLogger(__name__)


def offers_play_user(event, vk):
    vk.messages.send(
        user_id=event.user_id,
        message="Привет! Я бот для викторин!",
        keyboard=get_custom_keyboard(),
        random_id=random.randint(1, 1000)
    )


def handle_new_question_request(event, vk, questions, redis_conn):
    random_num_question = random.choice(
        list(questions)
    )
    question, answer = questions[random_num_question]
    user_id = event.user_id
    vk.messages.send(
        user_id=user_id,
        message=question,
        keyboard=get_custom_keyboard(),
        random_id=random.randint(1, 1000)
    )
    user = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
    }
    redis_conn.json().set(user_id, Path.root_path(), user)


def handle_solution_attempt(event, redis_conn, vk):
    user_id = event.user_id
    user_answer = event.text.lower()
    quiz_answer = redis_conn.json().get(
        user_id
    )['answer'].lower().split(':')[-1]
    similarity_value_number = difflib.SequenceMatcher(
        lambda x: x == " ",
        user_answer,
        quiz_answer
    ).ratio()
    words_similarity_score = 0.80
    if similarity_value_number > words_similarity_score:
        vk.messages.send(
            user_id=event.user_id,
            message='Правильно! Поздравляю! '
            'Для следующего вопроса нажми «Новый вопрос».',
            keyboard=get_custom_keyboard(),
            random_id=random.randint(1, 1000)
        )
    if similarity_value_number < words_similarity_score:
        vk.messages.send(
            user_id=event.user_id,
            message='Неправильно… Попробуешь ещё раз?',
            keyboard=get_custom_keyboard(),
            random_id=random.randint(1, 1000)
        )


def sends_message_surrendered(redis_conn, vk, event):
    user_id = event.user_id
    quiz_answer = redis_conn.json().get(user_id)['answer']
    vk.messages.send(
        user_id=event.user_id,
        message=quiz_answer,
        keyboard=get_custom_keyboard(),
        random_id=random.randint(1, 1000)
    )


def get_custom_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет')
    return keyboard.get_keyboard()


def gets_args():
    parser = argparse.ArgumentParser('accepts optional args')
    parser.add_argument(
        "-fp", "--file_path",
        help="in enter your path to the file",
        default=os.path.join('archive', random.choice(os.listdir('archive')))
    )
    args = parser.parse_args()
    return args


def main():
    """ Пример создания клавиатуры для отправки ботом """
    env = Env()
    env.read_env()
    vk_token = env.str("VK_GROUP_TOKEN")
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()

    redis_port = env.str("REDIS_PORT")
    redis_pass = env.str("REDIS_PASS")
    redis_host = env.str("REDIS_HOST")
    redis_conn = redis.StrictRedis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        charset="utf-8",
        decode_responses=True,
    )
    questions = gets_random_questions_answers(gets_args().file_path)
    longpoll = VkLongPoll(vk_session)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.info('VK бот запущен')
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text == 'play':
                        offers_play_user(event, vk)
                    elif event.text == 'Новый вопрос':
                        handle_new_question_request(
                            event, vk, questions, redis_conn)
                    elif event.text == 'Сдаться':
                        sends_message_surrendered(redis_conn, vk, event)
                        handle_new_question_request(
                            event, vk, questions, redis_conn)
                    else:
                        handle_solution_attempt(event, redis_conn, vk)
        except ConnectionError as connect_er:
            logger.warning(f'Произошёл сетевой сбой VK бота\n{connect_er}\n')
            sleep(20)


if __name__ == '__main__':
    main()
