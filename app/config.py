import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    db_file = Path(__file__).parent / "settings.json"
    images_path = Path(__file__).parent.parent / "images"


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Get logger and set a specific formatter."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s %(name)-15s %(levelname)-8s %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


project_settings = Settings()
