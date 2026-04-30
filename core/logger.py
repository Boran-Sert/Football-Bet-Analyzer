import logging
import json
import sys
from datetime import datetime
from typing import Any

class JsonFormatter(logging.Formatter):
    """Logs as JSON objects."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "logger": record.name
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)
            
        return json.dumps(log_record)

import logging.handlers
import queue

def setup_logging():
    """Configures the root logger for JSON output with a non-blocking QueueHandler."""
    # 1. Base Handler (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JsonFormatter())
    
    # 2. Queue for Async Logging (Faz 6 Fix: Senkron loglama darboğazı engellendi)
    log_queue = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    
    # 3. Listener to process logs in background
    listener = logging.handlers.QueueListener(log_queue, stream_handler)
    listener.start()
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers = [queue_handler]
    
    return logger

# Singleton logger instance
logger = setup_logging()
