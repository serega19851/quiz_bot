# -*- coding: utf-8 -*-
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from environs import Env
from vk_api.longpoll import VkLongPoll, VkEventType
import random
from redis.commands.json.path import Path
from config_radis import creates_table_users, connects_radis
import difflib
from questions_answers import gets_random_questions_answers
import logging
from time import sleep
from requests.exceptions import ReadTimeout, ConnectionError


logger = logging.getLogger(__name__)


def offers_play_user(event, vk):
    vk.messages.send(
        user_id=event.user_id,
        message="Привет! Я бот для викторин!",
        keyboard=get_custom_keyboard(),
        random_id=random.randint(1, 1000)
    )


def handle_new_question_request(event, vk, questions, conn_red):
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
    user_vk = creates_table_users(question, answer, user_id)[0]
    conn_red.json().set("bot_vk", Path.root_path(), user_vk)


def handle_solution_attempt(event, conn_red, vk):
    user_answer = event.text.lower()
    quiz_answer = conn_red.json().get(
            "user_vk"
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


def sends_message_surrendered(conn_red, vk, event):
    quiz_answer = conn_red.json().get("bot_vk")['answer']
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


def main():
    """ Пример создания клавиатуры для отправки ботом """
    env = Env()
    env.read_env()
    vk_token = env.str("VK_GROUP_TOKEN")
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    conn_redis = connects_radis()
    questions = gets_random_questions_answers()
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
                            event, vk, questions, conn_redis)
                    elif event.text == 'Сдаться':
                        sends_message_surrendered(conn_redis, vk, event)
                        handle_new_question_request(
                            event, vk, questions, conn_redis)
                    else:
                        handle_solution_attempt(event, conn_redis, vk)
        except ReadTimeout as timeout:
            logger.warning(f'Превышено время ожидания VK бота\n{timeout}\n')
        except ConnectionError as connect_er:
            logger.warning(f'Произошёл сетевой сбой VK бота\n{connect_er}\n')
            sleep(20)


if __name__ == '__main__':
    main()
