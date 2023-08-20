from environs import Env
import redis


def connects_radis():
    env = Env()
    env.read_env()
    portredis = env.str("PORTREDIS")
    passredis = env.str("PASSREDIS")
    hostredis = env.str("HOSTREDIS")

    conn_redis = redis.StrictRedis(
        host=hostredis,
        port=portredis,
        password=passredis,
        charset="utf-8",
        decode_responses=True,
    )
    return conn_redis


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
