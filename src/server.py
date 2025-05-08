import sys

sys.pycache_prefix = "../__pycache__"

from fastapi import FastAPI
from tortoise import Tortoise
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from routes import register_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        print("Tortoise ORM inicializado com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar Tortoise ORM: {str(e)}")
        raise
    yield

    # shutdown
    print("Fechando conexões do Tortoise ORM...")
    await Tortoise.close_connections()


app = FastAPI(title="Graphfy API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TORTOISE
TORTOISE_ORM = {
    "connections": {"default": "postgres://postgres:123456@localhost:5432/graphfy_db"},
    "apps": {
        "models": {
            "models": ["aerich.models", "db.models.user_model", "db.models.chat_model"],
            "default_connection": "default",
        }
    },
}
register_tortoise(
    app, config=TORTOISE_ORM, generate_schemas=False, add_exception_handlers=True
)

# ROUTES
register_routes(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
