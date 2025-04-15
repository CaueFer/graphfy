from dotenv import load_dotenv
from pathlib import Path
import os
import json
import httpx

from lib.default_constants import tempDf

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")


async def processData(prompt: str, sessionId: str):
    path = Path(f"{tempDf}{sessionId}.txt")
    path = path.resolve()

    print(path)
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
    chat_history.append({"role": "user", "content": prompt})

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

    response = data.get("message", {}).get("content", "")

    try:
        colunas = json.loads(response)
    except Exception:
        return {
            "error": "Não foi possível interpretar as colunas retornadas pela IA",
            "resposta_bruta": response,
            "success": False,
        }

    # History
    chat_history.append({"role": "assistant", "content": response})

    return {
        "success": True,
        "colunas": colunas,
    }
