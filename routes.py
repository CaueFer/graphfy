from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import httpx
import pandas as pd
import io
from typing import List, Optional
import json

router = APIRouter()

OLLAMA_URL = "http://localhost:11434/api/chat"

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

df_global: Optional[pd.DataFrame] = None


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
    global df_global

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
    df_global = limited_df.to_string(index=False)

    return {
        "message": "Arquivo recebido e analisado. Pronto para perguntas.",
        "preview": df_global,
        "instructions": "Agora envie uma pergunta como: 'Gere um gráfico dos macronutrientes'",
    }


@router.post("/processdata")
async def processData():
    global df_global

    # Prompt
    prompt = f"""
    Quero gerar um grafico sobre os macro nutrientes, quais colunas eu envio para meu grafico?
    
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
    print(response)

    try:
        colunas = json.loads(response)  # cuidado com segurança aqui
    except Exception:
        return {
            "error": "Não foi possível interpretar as colunas retornadas pela IA",
            "resposta_bruta": response,
        }

    chat_history.append({"role": "assistant", "content": response})
    
    gerar_grafico(colunas)

    return {
        "mensagem": f"Gráfico solicitado com base nas colunas: {colunas}",
        "colunas": colunas,
    }


def gerar_grafico(colunas: list[str]):
    print(colunas)
