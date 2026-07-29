"""Reusable base class for every pipeline in this codebase.

Anything a pipeline needs generically — a name, counters for processed
and skipped records, a log() helper, and a summary() report — lives
here so specialised pipelines can inherit it and focus on what makes
them different.
"""


class BasePipeline:
    """Base class for named, observable data pipelines.

    Subclasses supply their own name and implement run(). They inherit
    log(), summary(), and the processed/skipped counters automatically.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.processed = 0
        self.skipped = 0

    def log(self, message: str) -> None:
        """Prefix every message with the pipeline name for readability."""
        print(f"[{self.name}] {message}")

    def summary(self) -> None:
        """Print a human-readable run summary."""
        print(f"\n[{self.name}] Summary")
        print(f"  Processed : {self.processed}")
        print(f"  Skipped   : {self.skipped}")


if __name__ == "__main__":
    bp = BasePipeline("TestPipeline")
    bp.log("Hello from base")
    bp.processed = 3
    bp.skipped = 1
    bp.summary()
