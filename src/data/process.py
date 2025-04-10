from dotenv import load_dotenv
import os
import json
import httpx

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")


async def processData(prompt: str):
    global df_global

    # Prompt
    prompt = f"""
    prompt: {prompt}
    
    Tabela:
    {df_global}
    """

    # History
    chat_history.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            OLLAMA_URL,
            json={
                "model": "llama3:8b",
                "messages": chat_history,
                "stream": False,
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
        }

    # History
    chat_history.append({"role": "assistant", "content": response})

    return {
        "success": True,
        "colunas": colunas,
    }
