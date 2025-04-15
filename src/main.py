from fastapi import File, Form, UploadFile
from fastapi.responses import StreamingResponse
from typing import Optional
from pathlib import Path
import pandas as pd
import json
import io

from lib.default_constants import tempDf
from graph.generator import gera_grafico
from data.process import processData


async def start_chat_service(prompt: str, sessionId: str):
    try:
        if sessionId is None:
            return {"error": f"SessionId inválido"}

        generator = manager(prompt, sessionId)
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        return {"error": f"Erro ao iniciar chat: {str(e)}"}


async def manager(prompt: str, sessionId: str):
    try:
        yield f"data: {json.dumps({'status': 'Planilha recebida, processando dados...'})}\n\n"
        responseProcess = await processData(prompt)

        if responseProcess["error"] is not None:
            yield f"data: {json.dumps({'error': responseProcess['error']})}\n\n"
            return

        if responseProcess["success"] is True:
            colunas = responseProcess["colunas"]
            yield f"data: {json.dumps({'status': 'Dados processados, gerando gráfico...'})}\n\n"

        responseGraficos = await gera_grafico(colunas)

        if responseGraficos["error"] is not None:
            yield f"data: {json.dumps({'error': responseGraficos['error']})}\n\n"
            return

        if responseGraficos["success"] is True:
            yield f"data: {json.dumps({'status': 'Gráfico gerado com sucesso!'})}\n\n"
            yield f"data: {json.dumps({'graphValues': responseGraficos['graphValues']})}\n\n"
            return

    except Exception as e:
        yield f"data: {json.dumps({'error': f'Erro gerenciar: {str(e)}'})}"
        return


async def upload_spreadsheet_service(
    file: UploadFile = File(...),
    range: Optional[str] = Form(None),
    sessionId: str = Form(None),
):
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
                    return {
                        "error": "O valor do intervalo 'inicial' deve ser menor que 'final'."
                    }
            except ValueError:
                return {"error": "O parâmetro 'intervalo' inválido."}

        limited_df = df.iloc[start:end]  # [linhas, colunas] - so to passando linhas
        dataframe = limited_df.to_string(index=False)

        path = Path(f"{tempDf}{sessionId}.txt")
        path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(dataframe)

        if path.exists():
            return {
                "message": "Arquivo recebido e analisado. Pronto para perguntas.\n ",
                "instructions": "\n".join(
                    [
                        "Agora envie uma pergunta como: ",
                        "- Gerar um gráfico dos macronutrientes ",
                        "- Mostrar um gráfico com a evolução dos gastos mensais ",
                        "- Criar um gráfico de barras com a quantidade de participantes por evento ",
                        "- Gerar um gráfico de linha com o progresso das metas semanais ",
                    ]
                ),
                "success": True,
            }

        return {
            "message": "Erro ao receber o arquivo.",
            "instructions": None,
            "success": False,
        }

    except Exception as e:
        return {"error": f"Erro ao ler o arquivo: {str(e)}"}
