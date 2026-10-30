from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .lifespan import lifespan
from .settings import app_config

app = FastAPI(
    title="GENERATION SITE API",
    description="REST API панели генерации компаний и сайтов",
    version=app_config.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors_origins,
    allow_credentials=app_config.cors_allow_credentials,
    allow_methods=app_config.cors_allow_methods,
    allow_headers=app_config.cors_allow_headers,
)


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}
