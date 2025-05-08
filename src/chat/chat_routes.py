from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List

from chat.chat_services import upload_spreadsheet_service
from lib.helpers.jwt_helper import verify_token

chatRouter = APIRouter()


# UPLOAD SPREADSHEET
class UploadSpreadsheetRequest(BaseModel):
    worksheetRange: List[str]
    token: str

@chatRouter.post("/upload-spreadsheet")
async def upload_spreadsheet(
    body: UploadSpreadsheetRequest
):  
    try:
        if verify_token(token=body.token):
            response = await upload_spreadsheet_service(worksheetRange=body.worksheetRange)
            return response

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado.",
        )
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
