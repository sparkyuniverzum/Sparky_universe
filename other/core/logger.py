# app/core/logger.py
import logging
import structlog


def setup_logger():
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
    )

    return structlog.get_logger()
