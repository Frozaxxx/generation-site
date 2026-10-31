import uvicorn
from fastapi.staticfiles import StaticFiles

from src import preview_router, router
from src.core.fastapi import app
from src.core.settings import app_config, storage_config
from src.shared.api.exception_handler import setup_exception_handlers

app.include_router(router)
app.include_router(preview_router)

setup_exception_handlers(app)

# Фото команды и другие файлы компаний. Файлы сайтов отдаются своими ручками.
storage_config.media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=storage_config.media_dir), name="media")


if __name__ == "__main__":
    uvicorn.run(app, host=app_config.host, port=app_config.port)
