from redis.commands.json.path import Path
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from config_radis import creates_table_users, connects_radis
from telegram import ReplyKeyboardRemove, Update, ReplyKeyboardMarkup
from environs import Env
from questions_answers import gets_random_questions_answers
import random
from functools import partial
import logging
import difflib


logger = logging.getLogger(__name__)
NEWQUESTIONS, HANDLESOLUTIONATTEMPT = range(2)


def start(update: Update, context: CallbackContext):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(
        custom_keyboard,
        resize_keyboard=True
    )
    update.message.reply_text(
        "Привет! Я бот для викторин!", reply_markup=reply_markup)
    return NEWQUESTIONS


def handle_new_question_request(
        update: Update,
        context: CallbackContext,
        questions,
        conn_red
) -> int:

    random_num_question = random.choice(
        list(questions)
    )
    question, answer = questions[random_num_question]
    user_id = update.message.from_user.id
    user_tg = creates_table_users(question, answer, user_id)[1]
    conn_red.json().set("user_tg", Path.root_path(), user_tg)
    update.message.reply_text(
        f'{question}',
    )
    return HANDLESOLUTIONATTEMPT


def handle_solution_attempt(
        update: Update,
        context: CallbackContext,
        conn_red
):
    user_answer = update.message.text.lower()
    quiz_answer = conn_red.json().get(
            "user_tg"
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
        return NEWQUESTIONS

    if similarity_value_number < words_similarity_score:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')
        return HANDLESOLUTIONATTEMPT


def handles_user_surrender(
        update: Update,
        context: CallbackContext,
        questions,
        conn_red
):
    quiz_answer = conn_red.json().get("user_tg")['answer']
    update.message.reply_text(quiz_answer)
    random_num_question = random.choice(
        list(questions)
    )
    question, answer = questions[random_num_question]
    update.message.reply_text(question)
    user_id = update.message.from_user.id
    user_tg = creates_table_users(question, answer, user_id)[1]
    conn_red.json().set("user_tg", Path.root_path(), user_tg)
    return HANDLESOLUTIONATTEMPT


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye!', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def handle_error(update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


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

    conn_redis = connects_radis()
    questions = gets_random_questions_answers()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            NEWQUESTIONS: [
                MessageHandler(
                    Filters.regex(
                        '^Новый вопрос$'
                    ),
                    partial(
                        handle_new_question_request,
                        questions=questions,
                        conn_red=conn_redis
                    )
                ),
            ],

            HANDLESOLUTIONATTEMPT: [
                MessageHandler(Filters.regex('^Сдаться$'),
                               partial(
                    handles_user_surrender,
                    conn_red=conn_redis,
                    questions=questions,

                )
                ),
                CommandHandler('cancel', cancel),


                MessageHandler(
                    Filters.text,
                    partial(
                        handle_solution_attempt,
                        conn_red=conn_redis,

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
