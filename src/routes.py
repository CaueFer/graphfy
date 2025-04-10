from fastapi import APIRouter, HTTPException, UploadFile, File, Form

router = APIRouter()

from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import httpx
import io
import os

from main import start_chat_stream
from lib.default_constants import tempDf

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
async def upload_spreadsheet(file: UploadFile = File(...), range: Optional[str] = Form(None), sessionId: str = Form(None)):
    try:
        if file is None:
            return {"error": f"Arquivo inválido."}
        
        if sessionId is None:
            return {"error": f"SessionId inválido."}

        content = await file.read()

        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(content))
   

        if df.empty:
            return {"error": "O arquivo está vazio."}

        if range is None:
            start, end = 0, 20  # Padrão: primeiras 20 linhas
        else:
            try:
                start_str, end_str = range.split(",")
                start = int(start_str.strip())
                end = int(end_str.strip())
                if start >= end:
                    return {"error": "O valor do intervalo 'inicial' deve ser menor que 'final'."}
            except ValueError:
                return {"error": "O parâmetro 'intervalo' inválido."}

        limited_df =  df.iloc[start:end]  # [linhas, colunas] - so to passando linhas
        dataframe =  limited_df.to_string(index=False)
        
        path = Path(f"{tempDf}{sessionId}.txt")
        path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            f.write(dataframe)

        return {
            "message": "Arquivo recebido e analisado. Pronto para perguntas.",
            "instructions": "Agora envie uma pergunta como: 'Gerar um gráfico dos macronutrientes'",
            "success": True,
        }
    except Exception as e:
        return {"error": f"Erro ao ler o arquivo: {str(e)}"}


@router.post("/start-chat")
async def start_chat(prompt: str, sessionId: int):
    try:
        return await start_chat_stream(prompt, sessionId)
    except Exception as e:
        return {"error": f"Erro ao iniciar chat: {str(e)}"}
