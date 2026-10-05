import logging
import sys

logger = logging.getLogger("multi_llm")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log_stage(stage: str, message: str, **kwargs):
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"[{stage.upper()}] {message} {extra}".strip())
