import logging
import orjson
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "logger": record.name,
        }
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)

        # orjson.dumps byte döner, .decode() ile string'e çeviriyoruz.
        # OPTION_SERIALIZE_DATETIME sayesinde datetime nesneleri otomatik çözülür.
        return orjson.dumps(
            log_record, option=orjson.OPT_INDENT_2
        ).decode("utf-8")


import logging.handlers
import queue

_listener = None  # Module-level reference for shutdown


def setup_logging():
    """Configures the root logger for JSON output with a non-blocking QueueHandler."""
    global _listener
    # 1. Base Handler (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JsonFormatter())

    # 2. Queue for Async Logging (Faz 6 Fix: Senkron loglama darboğazı engellendi)
    log_queue = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)

    # 3. Listener to process logs in background
    listener = logging.handlers.QueueListener(log_queue, stream_handler)
    listener.start()
    _listener = listener

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers = [queue_handler]

    return logger


def shutdown_logging():
    """QueueListener'i guvenli sekilde durdurur. Uygulama shutdown'inda cagrilir."""
    global _listener
    if _listener:
        _listener.stop()
        _listener = None


# Singleton logger instance
logger = setup_logging()
