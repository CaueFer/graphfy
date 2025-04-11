from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI() 
app.include_router(router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("run:app", host="0.0.0.0", port=5000, reload=True)
