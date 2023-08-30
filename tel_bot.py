import argparse
import difflib
import logging
import os
import random
from functools import partial

import redis
from environs import Env
from redis.commands.json.path import Path
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

from questions_answers import gets_random_questions_answers

logger = logging.getLogger(__name__)
NEW_QUESTIONS, HANDLE_SOLUTION_ATTEMPT = range(2)


def start(update: Update, context: CallbackContext):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(
        custom_keyboard,
        resize_keyboard=True
    )
    update.message.reply_text(
        "Привет! Я бот для викторин!", reply_markup=reply_markup)
    return NEW_QUESTIONS


def handle_new_question_request(
        update: Update,
        context: CallbackContext,
        questions,
        redis_conn
) -> int:

    random_num_question = random.choice(
        list(questions)
    )
    question, answer = questions[random_num_question]
    user_id = update.message.from_user.id
    user = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
    }
    redis_conn.json().set(user_id, Path.root_path(), user)
    update.message.reply_text(question)
    return HANDLE_SOLUTION_ATTEMPT


def handle_solution_attempt(
        update: Update,
        context: CallbackContext,
        redis_conn
):
    user_id = update.message.from_user.id
    user_answer = update.message.text.lower()
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
        update.message.reply_text(
            'Правильно! Поздравляю! '
            'Для следующего вопроса нажми «Новый вопрос».'
        )
        return NEW_QUESTIONS

    if similarity_value_number < words_similarity_score:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')
        return HANDLE_SOLUTION_ATTEMPT


def handles_user_surrender(
        update: Update,
        context: CallbackContext,
        questions,
        redis_conn
):
    user_id = update.message.from_user.id
    quiz_answer = redis_conn.json().get(user_id)['answer']
    update.message.reply_text(quiz_answer)
    random_num_question = random.choice(
        list(questions)
    )
    question, answer = questions[random_num_question]
    update.message.reply_text(question)
    user = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
    }
    redis_conn.json().set(user_id, Path.root_path(), user)
    return HANDLE_SOLUTION_ATTEMPT


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye!', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def handle_error(update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def gets_args():
    parser = argparse.ArgumentParser('accepts optional args')
    parser.add_argument(
        "-fp", "--file_path",
        help="in enter your path to the file",
        default=os.path.join('archive', random.choice(os.listdir('archive')))
    )
    args = parser.parse_args()
    return args


def main() -> None:
    env = Env()
    env.read_env()
    tel_token = env.str("TELEGRAM_TOKEN")
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.setLevel(logging.INFO)
    updater = Updater(tel_token)
    dispatcher = updater.dispatcher

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
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            NEW_QUESTIONS: [
                MessageHandler(
                    Filters.regex(
                        '^Новый вопрос$'
                    ),
                    partial(
                        handle_new_question_request,
                        questions=questions,
                        redis_conn=redis_conn
                    )
                ),
            ],

            HANDLE_SOLUTION_ATTEMPT: [
                MessageHandler(Filters.regex('^Сдаться$'),
                               partial(
                    handles_user_surrender,
                    redis_conn=redis_conn,
                    questions=questions,

                )
                ),
                CommandHandler('cancel', cancel),


                MessageHandler(
                    Filters.text,
                    partial(
                        handle_solution_attempt,
                        redis_conn=redis_conn,

                    )
                ),

            ],

        },

        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(handle_error)
    logger.info('Телеграм бот запущен')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
