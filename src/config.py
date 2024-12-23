import logging
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from pathlib import Path


@dataclass
class Config:
    email: str | None
    password: str | None
    headless: bool = True
    timeout: int = 30
    response_max_wait: int = 60
    response_stable_interval: int = 2
    max_login_retries: int = 3
    log_level: str = "INFO"
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    log_file_name: str = "app.log"

    def setup_logging(self) -> None:
        self.log_dir.mkdir(exist_ok=True)
        log_file = self.log_dir / self.log_file_name

        level = getattr(logging, self.log_level.upper(), logging.INFO)

        logger = logging.getLogger(__name__)
        logger.setLevel(level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)

        file_handler = RotatingFileHandler(
            str(log_file), maxBytes=1_000_000, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)

        logger.handlers.clear()
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
