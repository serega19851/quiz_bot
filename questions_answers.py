def gets_random_questions_answers(path_file):
    questions_answers_ = {}
    questions_answers = []
    with open(path_file, "r", encoding="KOI8-R") as file:
        file_contents = file.read()

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
    for number, _ in enumerate(questions_answers):
        questions_answers_[number+1] = questions_answers[number]
    return questions_answers_
