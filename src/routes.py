from fastapi import APIRouter, HTTPException, UploadFile, File, Form

router = APIRouter()

from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import os

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


class ChatRequest(BaseModel):
    message: str


@router.get("/ping")
async def pong():
    return {"message": "pong!"}


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


@router.post("/upload-spreadsheet")
async def upload_spreadsheet(
    file: UploadFile = File(...),
    range: Optional[str] = Form(..., alias="range"),
    sessionId: str = Form(..., alias="sessionId"),
):
    try:
        response = await upload_spreadsheet_service(file, range, sessionId)
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
