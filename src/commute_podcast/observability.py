from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

LOGGER = logging.getLogger("commute_podcast")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "event": getattr(record, "event", record.getMessage()),
        }
        for name in ("episode_id", "chunk_id", "phase", "attempt", "status"):
            value = getattr(record, name, None)
            if value is not None:
                event[name] = value
        if record.exc_info:
            event["error"] = self.formatException(record.exc_info)
        return json.dumps(event)


def configure_logging(level: int = logging.INFO) -> None:
    if not LOGGER.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        LOGGER.addHandler(handler)
    LOGGER.setLevel(level)
    LOGGER.propagate = False


def log_event(event: str, **fields: Any) -> None:
    LOGGER.info(event, extra={"event": event, **fields})
