from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from typing import List

from chat.chat_services import (
    upload_spreadsheet_service,
    get_chat_service,
    get_chat_messages_service,
)
from lib.helpers.jwt_helper import verify_token, verify_token_from_http

chatRouter = APIRouter(dependencies=[Depends(verify_token_from_http)])


# UPLOAD SPREADSHEET
class UploadSpreadsheetRequest(BaseModel):
    worksheetRange: List[str]


@chatRouter.post("/upload-spreadsheet")
async def upload_spreadsheet(request: Request):
    try:
        auth_header = request.headers.get("authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")

        token = auth_header.split(" ")[1]
        payload = verify_token(token=token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Não autorizado.",
            )

        body = await request.json()

        response = await upload_spreadsheet_service(
            worksheetRange=body["worksheetRange"], user_id=payload["user"]["id"]
        )
        return response

    except Exception as e:
        print(f"Erro em upload-spreadsheet: {str(e)}")
        return {"error": f"Erro ao enviar o arquivo: {str(e)}"}


class ChatStreamRequest(BaseModel):
    prompt: str
    sessionId: str


@chatRouter.post("/start-chat")
async def start_chat(body: ChatStreamRequest):
    try:
        prompt = body.prompt
        sessionId = body.sessionId

        return await start_chat_service(prompt, sessionId)
    except Exception as e:
        return {"error": f"Erro ao iniciar chat: {str(e)}"}


class GetChatRequest(BaseModel):
    chat_id: str


@chatRouter.post("/get-chat")
async def get_chat(body: GetChatRequest):
    try:
        chat_id = body.chat_id

        chat = await get_chat_service(chat_id)

        if chat is None:
            return {"success": False}

        return {"success": True}

    except Exception as e:
        print("Erro em inicializar chat: ",e)
        return {"error": f"Erro em inicializar chat."}

@chatRouter.post("/get-chat-messages")
async def get_chat_messages(body: GetChatRequest):
    try:
        chat_id = body.chat_id

        msgs = await get_chat_messages_service(chat_id)

        return {"msgs": msgs}

    except Exception as e:
        return {"error": f"Erro em receber mensagens do chat."}
