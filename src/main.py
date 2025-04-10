from fastapi.responses import StreamingResponse
import json

from data.process import processData
from graph.generator import gera_grafico


async def start_chat_stream(prompt: str, sessionId: int):
    try:
        if sessionId is None:
            return {"error": f"SessionId inválido"}

        return StreamingResponse(
            manager(prompt, sessionId), media_type="text/event-stream"
        )
    except Exception as e:
        return {"error": f"Erro ao iniciar chat: {str(e)}"}


async def manager(prompt: str, sessionId: int):
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
