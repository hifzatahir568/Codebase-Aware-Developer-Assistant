import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set


@dataclass
class Settings:
    app_title: str = "Codebase Aware Developer Assistant"
    db_path: str = field(default_factory=lambda: os.getenv("RAG_DB_PATH", "./rag_index.db"))
    frontend_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2] / "frontend")

    embed_model_id: str = field(
        default_factory=lambda: os.getenv("EMBED_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")
    )
    llm_model_id: str = field(default_factory=lambda: os.getenv("LLM_MODEL_ID", "distilgpt2"))

    ignore_folders: Set[str] = field(
        default_factory=lambda: {
            ".git",
            ".idea",
            ".vscode",
            "__pycache__",
            "venv",
            ".venv",
            "node_modules",
            "dist",
            "build",
            ".mypy_cache",
            ".pytest_cache",
            "codebase",
        }
    )
    include_extensions: Set[str] = field(
        default_factory=lambda: {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".env"}
    )

    max_file_bytes: int = field(default_factory=lambda: int(os.getenv("MAX_FILE_BYTES", "2000000")))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1200")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "200")))
    default_top_k: int = field(default_factory=lambda: int(os.getenv("DEFAULT_TOP_K", "5")))
    max_top_k: int = field(default_factory=lambda: int(os.getenv("MAX_TOP_K", "8")))
    default_max_context_chars: int = field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_CONTEXT_CHARS", "2000")))

    api_keys: Set[str] = field(
        default_factory=lambda: {k.strip() for k in os.getenv("RAG_API_KEYS", "changeme-dev-key").split(",") if k.strip()}
    )
    auth_enabled: bool = field(default_factory=lambda: os.getenv("AUTH_ENABLED", "1") == "1")

    rate_limit_enabled: bool = field(default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "1") == "1")
    rate_limit_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")))

    test_mode: bool = field(default_factory=lambda: os.getenv("TEST_MODE", "0") == "1")


settings = Settings()
