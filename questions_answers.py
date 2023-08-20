import random
import os


def gets_random_questions_answers():
    path_file = os.path.join('archive', random.choice(os.listdir('archive')))
    num_questions_answers = {}
    questions_answers = []
    with open(path_file, "r", encoding="KOI8-R") as my_file:
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

    return num_questions_answers
