from environs import Env
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
ENCODING = "KOI8-R"


def get_questions_answers(path_file):
    num_questions_answers = {}
    questions_answers = []
    with open(path_file, "r", encoding=ENCODING) as my_file:
        file_contents = my_file.read()
    for text in file_contents.split('\n\n'):
        if 'Вопрос ' in text:
            questions_answers.append(text)

        if 'Ответ:' in text:
            questions_answers.append(text)

    questions_answers = [
        [question, answer]for question, answer in zip(
            questions_answers[0::2], questions_answers[1::2]
        )
    ]

    for num in range(len(questions_answers)):
        num_questions_answers[num+1] = questions_answers[num]
    print(num_questions_answers)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text("Здравствуйте")


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def main() -> None:
    """Start the bot."""
    env = Env()
    env.read_env()

    telegram_token = env.str("TELEGRAM_TOKEN")
    # project_id = env.str("PROJECT_ID")
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, echo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
