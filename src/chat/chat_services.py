from dotenv import load_dotenv

from fastapi.responses import StreamingResponse
from pathlib import Path
from typing import List
from uuid import UUID
import asyncio
import httpx
import json
import os

from db.models.chat_model import Chat, Mensagem, Role
from graph.services.generator import graph_generator
from lib.default_constants import tempDf

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")


# ================ GET
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


# ================ POST/PUT
async def upload_spreadsheet_service(worksheetRange: List[str], user_id: str):
    try:
        if worksheetRange is None:
            return {"error": f"Dados planilha inválidos."}

        chat_count = await Chat.filter(user_id=int(user_id)).count()
        chat = await Chat.create(
            user_id=int(user_id), name=f"Nova Conversa {chat_count + 1}"
        )

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


async def start_chat_service(prompt: str, chat_id: str):
    try:
        if chat_id is None:
            return {"error": f"Id do chat inválido"}

        generator = manager(prompt, chat_id)
        return StreamingResponse(generator, media_type="text/event-stream")

    except Exception as e:
        return {"error": f"Erro ao iniciar chat: {str(e)}"}


async def manager(prompt: str, chat_id: int):
    try:
        yield json.dumps({"status": "Planilha recebida, processando dados..."}) + "\n\n"

        # delay fake
        await asyncio.sleep(3)

        responseProcess = await process_data_service(prompt, chat_id)

        print(responseProcess)

        if responseProcess["error"] is not None:
            yield json.dumps({"error": responseProcess["error"]}) + "\n\n"
            return

        if responseProcess["success"] is True:
            columns = responseProcess["columns"]
            yield json.dumps(
                {"status": "Dados processados, gerando gráfico..."}
            ) + "\n\n"

        # delay fake
        await asyncio.sleep(3)

        graphTitle = responseProcess["graphTitle"]
        columns = responseProcess["columns"]
        message = responseProcess["message"]
        yield json.dumps(
            {
                "status": "Gráfico gerado com sucesso!",
                "message": message,
                "graphTitle": graphTitle,
                "columns": columns,
            }
        ) + "\n\n"
    except Exception as e:
        yield json.dumps({"error": f"Erro gerenciar: {str(e)}"}) + "\n\n"
        return


async def process_data_service(userPrompt: str, chat_id: int):
    path = Path(f"{tempDf}{chat_id}.txt")
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
    system: 
    TASK: Voce precisa analisar a "Tabela" e retornar as colunas X e Y para eu gerar um grafico a partir disso.

    Retorne APENAS um JSON (nada mais alem do json) com estritamente o seguinte formato, seguir exatamente este formato. (CADA X PRECISA SER UM OBJETO NOVO DENTRO DE COLUMNS, Y SEMPRE PRECISAR SER UM NUMERO):
    FORMAT:(\"{{
        \\\"title\\\": \\\"Titulo do grafico aqui\\\",
        \\\"message\\\": \\\"Resumo do que o grafico esta mostrando (max de 5 palavras)\\\",
        \\\"columns\\\": [
            {{
                \\\"x\\\": \\\"valor do x1\\\",
                \\\"y\\\": \\\"numero do y1\\\",
            }}
        ]
    }}\")

    EXAMPLE: 
    \"exemploColumn = [
        {{ x: valor X, y: valor do Y, y: outro valor de Y, y: fazer assim para todos os valores de Y }},
        {{ x: valor X, y: valor do Y, y: outro valor de Y, y: fazer assim para todos os valores de Y }},
        {{ x: valor X, y: valor do Y, y: outro valor de Y, y: fazer assim para todos os valores de Y }}
    ]\"

    prompt: {userPrompt}
    
    Tabela:
    {userTable}
    """

    # History
    messages = await Mensagem.filter(chat_id=chat_id).order_by("-created_at").limit(10)

    chat_history = []
    if messages:
        for msg in messages:
            chat_history.append({"role": str(msg.role.value), "content": msg.content})

    # Add msg to history
    mensagem_dict = {"role": "user", "content": prompt}
    chat_history.append(mensagem_dict)

    await Mensagem.create(chat_id=UUID(chat_id), role=Role.user, content=userPrompt)

    # Receive llama response
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                OLLAMA_URL,
                json={
                    "model": "llama3:8b",
                    "messages": chat_history,
                    "stream": True,
                },
            ) as response:
                full_response = ""
                async for line in response.aiter_lines():
                    if line.strip():
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        full_response += content

        response = full_response
    except Exception as e:
        print("Erro llama", e)
        return {
            "error": "Erro conexão com llama",
            "success": False,
        }

    try:
        print(response)
        parsed = json.loads(response)
        print(parsed)

        graphTitle = parsed["title"]
        message = parsed["message"]
        columns = parsed["columns"]
    except Exception as e:
        print("Error response loads do llama: ", e)
        return {
            "error": "Não foi possível interpretar as colunas retornadas pela IA. Tente ser mais especifico.",
            "success": False,
        }

    # History
    mensagem_dict = {"role": "assistant", "content": message}
    await Mensagem.create(chat_id=UUID(chat_id), role=Role.assistant, content=response)

    return {
        "success": True,
        "error": None,
        "message": message,
        "graphTitle": graphTitle,
        "columns": columns,
    }


# ================ POST/PUT
async def delete_chat_service(chat_id: str):
    path = Path(f"{tempDf}{chat_id}.txt")
    path = path.resolve()
    if path.exists():
        path.unlink()

    chat_id_uuid = UUID(chat_id)
    await Chat.filter(id=chat_id_uuid).delete()
