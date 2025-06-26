from fastapi import APIRouter, HTTPException, FastAPI

from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import os

from auth.auth_routes import authRouter
from chat.chat_routes import chatRouter

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


class ChatRequest(BaseModel):
    message: str


# testar ollama
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


def register_routes(app: FastAPI):
    app.include_router(router, prefix="/api", tags=["general"])
    app.include_router(authRouter, prefix="/api/auth", tags=["auth"])
    app.include_router(chatRouter, prefix="/api/chat", tags=["chat"])
