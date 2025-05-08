from fastapi import APIRouter, HTTPException, Form, FastAPI

from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import os

from auth.auth_routes import authRouter
from data.services.management import start_chat_service
from data.services.management import upload_spreadsheet_service

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")


chat_history = [
    {
        "role": "system",
        "content": (
            "Você é um analista de dados. Receberá tabelas (em texto), Responda sempre em português (pt-BR), "
            "responda apenas com os nomes das colunas relevantes para gerar o gráfico ou análise. "
            "Formate a resposta como um JSON. No formato: ['nome coluna', 'nome coluna']"
        ),
    },
]


router = APIRouter()


# TESTAR BACKEND
@router.get("/ping")
async def pong():
    return {"message": "pong!"}


def register_routes(app: FastAPI):
    app.include_router(router, prefix="/api", tags=["general"])
    app.include_router(authRouter, prefix="/api/auth", tags=["auth"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_URL,
                json={"model": "llama3", "prompt": request.message, "stream": False},
            )

        response_json = response.json()
        return {"response": response_json.get("response", "Erro ao gerar resposta")}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro na comunicação com Ollama: {str(e)}"
        )


# UPLOAD SPREADSHEET
@router.post("/upload-spreadsheet")
async def upload_spreadsheet(
    workesheetRange: List[str] = Form(..., alias="range"),
    token: str = Form(..., alias="token"),
):
    try:
        response = await upload_spreadsheet_service(workesheetRange, token)
        return response
    except Exception as e:
        print(f"Erro em upload-spreadsheet: {str(e)}")
        return {"error": f"Erro ao enviar o arquivo: {str(e)}"}


class ChatStreamRequest(BaseModel):
    prompt: str
    sessionId: str


@router.post("/start-chat")
async def start_chat(body: ChatStreamRequest):
    try:
        prompt = body.prompt
        sessionId = body.sessionId

        return await start_chat_service(prompt, sessionId)
    except Exception as e:
        return {"error": f"Erro ao iniciar chat: {str(e)}"}
