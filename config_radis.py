def creates_table_users(question, answer, user_id):

    user_vk = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
    }
    user_tg = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
    }

    return user_vk, user_tg
