"""
Section 1.8 — Production Python: Logging.

Print statements do not exist in production. Three reasons:

  1. Print output disappears — no record of what happened.
     When a pipeline fails at 3am there is nothing to look back at.
  2. Print has no levels — you cannot distinguish "just informational"
     from "critical failure".
  3. Print cannot be routed to files, monitoring, or alerting tools.

The `logging` module fixes all three. This file demonstrates the
minimum production-ready setup a DE should reach for.

Run: `python 09_production_logging.py`
"""

import logging
from logging.handlers import RotatingFileHandler


def configure_root_logger(
    level: int = logging.INFO,
    log_file: str | None = None,
) -> logging.Logger:
    """Configure the root logger with a formatter and optional file handler.

    In real projects this lives in a `setup_logging()` function called
    once at process startup. Every module then obtains a logger via
    `logging.getLogger(__name__)`.
    """
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        # Rotating handler: cap file size at ~1 MB, keep last 3 files.
        # Prevents log files from consuming disk indefinitely.
        handlers.append(
            RotatingFileHandler(
                log_file,
                maxBytes=1_000_000,
                backupCount=3,
            )
        )

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
        force=True,  # override any earlier config
    )

    return logging.getLogger()


def demo_log_levels() -> None:
    """Show the five standard levels and when each is used."""
    logger = logging.getLogger("demo_levels")

    logger.debug("Detailed information — only useful when debugging")
    logger.info("Pipeline started — normal operation")
    logger.warning("Something unexpected — pipeline still running")
    logger.error("Something failed — needs attention")
    logger.critical("Pipeline is down — immediate action needed")


def demo_structured_logging_pattern() -> None:
    """Log with contextual key-value data — the pattern used in real pipelines."""
    logger = logging.getLogger("pipeline")

    logger.info("Job started", extra={"job_id": 12345, "stage": "extract"})

    # Use %-style formatting inside logger calls — the logger only
    # formats the message if the level is enabled, which is faster than
    # building the string with f-strings for high-volume debug logs.
    record_count = 5000
    logger.info("Extracted %d records", record_count)


def demo_error_context() -> None:
    """Preserve exception traceback with logger.exception()."""
    logger = logging.getLogger("pipeline")

    try:
        int("not_a_number")
    except ValueError:
        # `logger.exception` automatically attaches the traceback.
        # Use this inside except blocks — never lose the stack trace.
        logger.exception("Failed to parse value")


def demo_named_loggers() -> None:
    """Different modules get different named loggers — filterable in production."""
    extractor = logging.getLogger("pipeline.extractor")
    transformer = logging.getLogger("pipeline.transformer")
    loader = logging.getLogger("pipeline.loader")

    extractor.info("Reading source file")
    transformer.info("Applying business rules")
    loader.info("Writing to warehouse")

    # In production you can turn OFF logs from noisy modules while
    # keeping others visible — invaluable when debugging.
    # Example:
    #     logging.getLogger("pipeline.transformer").setLevel(logging.WARNING)


def main() -> None:
    configure_root_logger(level=logging.DEBUG)

    print("=" * 60)
    print("LOG LEVELS")
    print("=" * 60)
    demo_log_levels()

    print("\n" + "=" * 60)
    print("STRUCTURED LOGGING")
    print("=" * 60)
    demo_structured_logging_pattern()

    print("\n" + "=" * 60)
    print("EXCEPTION LOGGING")
    print("=" * 60)
    demo_error_context()

    print("\n" + "=" * 60)
    print("NAMED LOGGERS")
    print("=" * 60)
    demo_named_loggers()


if __name__ == "__main__":
    main()
