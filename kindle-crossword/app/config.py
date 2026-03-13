from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    database_path: str = "./data/kindle_crossword.db"
    upload_path: str = "./data/uploads"
    output_path: str = "./data/output"

    # Auth: set APP_PASSWORD env var to require login
    app_password: str = ""
    secret_key: str = "change-me-in-production"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    kindle_email: str = ""

    auto_perspective: bool = True
    threshold_mode: str = "adaptive"
    contrast_clip_limit: float = 3.0
    sharpness: float = 1.2

    model_config = {"env_file": ".env"}

    def ensure_dirs(self) -> None:
        for path_str in (self.upload_path, self.output_path):
            Path(path_str).mkdir(parents=True, exist_ok=True)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
