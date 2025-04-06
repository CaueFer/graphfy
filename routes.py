from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import httpx
import pandas as pd
import io
from typing import List, Optional

router = APIRouter()

OLLAMA_URL = "http://localhost:11434/api/chat"

chat_history = [ 
    {
        "role": "system",
        "content": (
            "Você é um analista de dados. Receberá tabelas (em texto), Responda sempre em português (pt-BR), "
            "e deve fornecer insights úteis e claros. Seja direto, identifique padrões, médias, totais ou anomalias."
            "vou enviar a tabela abaixo:"
        )
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
async def upload_spreadsheet(file: UploadFile = File(...), range: Optional[str] = None):
    content = await file.read()

    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        return {"error": f"Erro ao ler o arquivo: {str(e)}"}

    if df.empty:
        return {"error": "O arquivo está vazio ou não pôde ser lido."}

    if range is None:
        start, end = 0, 20  # Padrão: primeiras 20 linhas
    else:
        try:
            start_str, end_str = range.split(",")
            start = int(start_str.strip())
            end = int(end_str.strip())
            if start >= end:
                return {"error": "O valor de 'start' deve ser menor que 'end'."}
        except ValueError:
            return {
                "error": "O parâmetro 'range' deve ser uma string no formato 'start,end' (ex.: '0,20')."
            }

    limited_df = df.iloc[start:end]
    table_text = limited_df.to_string(index=False)

    # Prompt
    prompt = f"""
    Tabela:
    {table_text}
    """
    
    # History
    chat_history.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            OLLAMA_URL,
            json={
                "model": "llama3:8b",
                "messages": chat_history,
                "stream": False
            }
        )
        data = res.json()

    reply = data["message"]["content"]
    chat_history.append({"role": "assistant", "content": reply})

    return {"response": reply}
