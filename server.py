from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_URL, json={
                "model": "llama3",
                "prompt": request.message,
                "stream": False
            })

        response_json = response.json()
        return {"response": response_json.get("response", "Erro ao gerar resposta")}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na comunicação com Ollama: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
