from dotenv import load_dotenv
from tortoise import Tortoise
from pathlib import Path
import os
import json
import httpx

from lib.default_constants import tempDf
from data.db.data_db import insert_mensagem_db, get_mensagens_db

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")


async def process_data_service(prompt: str, sessionId: str, chat_id: int):
    path = Path(f"{tempDf}{sessionId}.txt")
    path = path.resolve()

    if path.exists() is False:
        return {
            "error": "Planilha nao encontrada.",
            "resposta_bruta": None,
            "success": False,
        }

    userTable = path.read_text()

    # Prompt
    prompt = f"""
    prompt: {prompt}
    
    Tabela:
    {userTable}
    """

    # History
    total, rows = await get_mensagens_db(chat_id)

    if rows:
        chat_history = [dict(row) for row in rows]
    else:
        chat_history = []

    mensagem_dict = {"role": "user", "content": prompt}
    chat_history.append(mensagem_dict)
    await insert_mensagem_db(chat_id, json.dumps(mensagem_dict))

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                OLLAMA_URL,
                json={
                    "model": "llama3:8b",
                    "messages": chat_history,
                    "stream": True,
                },
            )
            data = res.json()
            print(data)
        response = data.get("message", {}).get("content", "")
    except Exception:
        return {
            "error": "Erro conexão com llama",
            "success": False,
        }

    print(response)
    try:
        colunas = json.loads(response)
    except Exception:
        return {
            "error": "Não foi possível interpretar as colunas retornadas pela IA",
            "resposta_bruta": response,
            "success": False,
        }

    # History
    mensagem_dict = {"role": "assistant", "content": response}
    resposta = json.dumps(mensagem_dict)
    await insert_mensagem_db(chat_id, resposta)

    return {
        "success": True,
        "colunas": colunas,
    }
