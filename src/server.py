from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

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

register_tortoise(
    app,
    db_url="postgres://postgres:123456@localhost:5432/graphfy_db",
    modules={"models": ["db.models.chat_model"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
