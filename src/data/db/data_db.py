from tortoise import Tortoise


async def get_mensagens_db(chat_id: int):
    return await Tortoise.get_connection("default").execute_query(
        """
            select 	
                id,
                mensagem
            from mensagem m
            where
                m.chat_id = $1
            ORDER BY m.sended_at DESC
            LIMIT 10
        """,
        [chat_id],
    )


async def insert_mensagem_db(chat_id: int, mensagem: str):
    return await Tortoise.get_connection("default").execute_query(
        """
        INSERT INTO mensagem (chat_id, mensagem, sended_at)
        VALUES ($1, $2, now())
        """,
        [chat_id, mensagem],
    )
