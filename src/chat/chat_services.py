from dotenv import load_dotenv

from fastapi.responses import StreamingResponse
from pathlib import Path
from typing import List
from uuid import UUID
import httpx
import json
import os

from chat.chat_db import insert_mensagem_db, get_mensagens_db
from db.models.chat_model import Chat, Mensagem, Role
from graph.services.generator import gera_grafico
from lib.default_constants import tempDf

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")


async def start_chat_service(prompt: str, sessionId: str):
    try:
        if sessionId is None:
            return {"error": f"SessionId inválido"}

        chat_id = await verify_chat_service(sessionId)

        if chat_id is not None:
            generator = manager(prompt, sessionId, chat_id)
            return StreamingResponse(generator, media_type="text/event-stream")

        return {"error": f"Erro ao iniciar chat: {str(e)}"}
    except Exception as e:
        return {"error": f"Erro ao iniciar chat: {str(e)}"}


async def verify_chat_service(sessionId: str):
    try:
        chat = await Chat.filter(session_id=sessionId).first()
        if not chat:
            chat = await Chat.create(session_id=sessionId)
        return chat.id

    except Exception as e:
        return {"error": f"Erro ao validar chat: {str(e)}"}


async def manager(prompt: str, sessionId: str, chat_id: int):
    try:
        yield json.dumps({"status": "Planilha recebida, processando dados..."}) + "\n\n"

        responseProcess = await process_data_service(prompt, sessionId, chat_id)

        if responseProcess["error"] is not None:
            yield json.dumps({"error": responseProcess["error"]}) + "\n\n"
            return

        if responseProcess["success"] is True:
            colunas = responseProcess["colunas"]
            yield json.dumps(
                {"status": "Dados processados, gerando gráfico..."}
            ) + "\n\n"
        responseGraficos = await gera_grafico(colunas)

        if responseGraficos["error"] is not None:
            yield json.dumps({"error": responseGraficos["error"]}) + "\n\n"
            return

        if responseGraficos["success"] is True:
            yield json.dumps(
                {"status": "Gráfico gerado com sucesso!"}, {"success": True}
            ) + "\n\n"
            yield json.dumps({"graphValues": responseGraficos["graphValues"]}) + "\n\n"
            return

    except Exception as e:
        yield json.dumps({"error": f"Erro gerenciar: {str(e)}"}) + "\n\n"
        return


async def upload_spreadsheet_service(worksheetRange: List[str], user_id: str):
    try:
        if worksheetRange is None:
            return {"error": f"Dados planilha inválidos."}

        chat_count = await Chat.filter(user_id=int(user_id)).count()
        chat = await Chat.create(user_id=int(user_id), name=f"Nova Conversa {chat_count + 1}")

        path = Path(f"{tempDf}{chat.id}.txt")
        path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        worksheetString = ", ".join(worksheetRange)
        with open(path, "w") as f:
            f.write(
                worksheetString
            )  # preciso passar obrigatorio como string para o write funfar

        if path.exists():
            msg = Mensagem(
                chat_id=chat.id,
                content=(
                    "Arquivo recebido e analisado. Pronto para perguntas.\n\n"
                    + "\n".join(
                        [
                            "Agora envie uma pergunta como:",
                            "- Gerar um gráfico dos macronutrientes",
                            "- Mostrar um gráfico com a evolução dos gastos mensais",
                            "- Criar um gráfico de barras com a quantidade de participantes por evento",
                            "- Gerar um gráfico de linha com o progresso das metas semanais",
                        ]
                    )
                ),
                role=Role.system,
                name="initial message",
            )

            await msg.save()

            return {
                "success": True,
                "chat_id": chat.id,
            }

        return {
            "success": False,
            "chat_id": None,
        }

    except Exception as e:
        return {"error": f"Erro ao ler o arquivo: {str(e)}"}


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


async def get_chat_service(chat_id: str):
    chat_id_uuid = UUID(chat_id)
    chat = await Chat.filter(id=chat_id_uuid).first()

    return chat


async def get_chat_messages_service(chat_id: str):
    msgs = await Mensagem.filter(chat_id=chat_id).order_by("-created_at").limit(15)

    return msgs


async def get_user_chats_service(user_id: str):
    chats = await Chat.filter(user_id=user_id).order_by("-created_at")

    return chats