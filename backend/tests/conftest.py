import os
import tempfile

# База и файлы тестов живут во временной папке, до импорта настроек приложения.
os.environ.setdefault("STORAGE_DATA_DIR", tempfile.mkdtemp(prefix="generation-site-tests-"))
os.environ.setdefault("OPENROUTER_API_KEY", "sk-or-test-secret-key")
