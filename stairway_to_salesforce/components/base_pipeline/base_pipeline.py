import argparse
import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Any

import dlt
from dlt.pipeline.pipeline import Pipeline
from dlt.sources.filesystem import filesystem, read_csv


class BasePipeline(ABC):
    """
    Standardized base class for the Stairway to Salesforce project.
    Handles CLI arguments, logging, Salesforce credential routing,
    and optional CSV file path management.
    """

    # --- 1. INITIALIZATION ---
    def __init__(
        self,
        pipeline_base_name: str,
        default_csv_path: str | None = None,
        verbose: bool = True,
    ):
        self.pipeline_base_name = pipeline_base_name
        self.default_csv_path = default_csv_path

        # Configure logging once; verbose controls whether INFO reaches the console.
        self._setup_logging()

        # Parse CLI arguments — --verbose flag overrides the constructor default.
        self.args = self._setup_and_parse_args(default_verbose=verbose)
        self.verbose: bool = self.args.verbose

        # pipeline_name is used as the logger name: meaningful in output,
        # reveals nothing about internal package structure.
        self.env: str = self.args.env
        self.pipeline_name = f"{self.pipeline_base_name}_{self.env}"
        self.logger = logging.getLogger(self.pipeline_name)
        self.logger.setLevel(logging.INFO if self.verbose else logging.WARNING)

        # Private storage for properties
        self._sf_credential_path = f"salesforce.{self.env}"
        self._csv_file_path = getattr(self.args, "csv_file", default_csv_path)

    # --- 2. PROPERTIES (Getters) ---
    @property
    def sf_credential_path(self) -> str:
        """Get the DLT secret path for Salesforce credentials based on environment."""
        return self._sf_credential_path

    @property
    def csv_path(self) -> str:
        """
        Return the validated, existing CSV file path.

        Raises:
            ValueError: if no path was provided, or the file is empty.
            FileNotFoundError: if the resolved path does not exist on disk.
        """
        if not self._csv_file_path or not isinstance(self._csv_file_path, str):
            raise ValueError(
                f"Pipeline '{self.pipeline_name}' requires a CSV file path, "
                "but none was provided via CLI arguments or default configuration."
            )

        full_path = os.path.join(os.getcwd(), self._csv_file_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(
                f"Source file not found: '{full_path}'. "
                "Check DEFAULT_CSV_PATH and your working directory."
            )

        if os.path.getsize(full_path) == 0:
            raise ValueError(f"Source file is empty (0 bytes): '{full_path}'.")

        return self._csv_file_path

    # --- 3. PUBLIC METHODS ---
    def get_credentials(self, basepath: str) -> Any:
        """
        Fetch credentials from dlt secrets using the current environment.
        Example: get_credentials("postgres") -> dlt.secrets["postgres.dev"]
        """
        credential_path = f"{basepath}.{self.env}"
        try:
            return dlt.secrets[credential_path]
        except KeyError as e:
            raise KeyError(
                f"Credentials not found at '{credential_path}'. Check your .dlt/secrets.toml file."
            ) from e

    def build_csv_source(self) -> Any:
        """
        Validate the CSV file and return a ready-to-use DLT source.

        Performs existence, size, and row-count checks, then returns a fresh
        unconsumed source. The smoke-test consumes one iterator; a second
        independent one is returned — filesystem() | read_csv() is lazy and
        stateless so each call produces a fresh iterator.

        Returns:
            A DLT pipe expression: filesystem(...) | read_csv()

        Raises:
            FileNotFoundError / ValueError: from csv_path if file is missing or empty.
            ValueError: if the source yields 0 data rows.
        """
        csv_path = self.csv_path
        bucket_url = csv_path.rsplit("/", 1)[0]
        file_glob = csv_path.rsplit("/", 1)[1]

        def _source():
            return filesystem(bucket_url=bucket_url, file_glob=file_glob) | read_csv()

        row_count = sum(1 for _ in _source())
        if row_count == 0:
            raise ValueError(
                f"Source for pipeline '{self.pipeline_name}' yielded 0 rows. "
                "The file may have no data rows or an unreadable format."
            )

        self.logger.info("Source file '%s' validated: %d row(s) found.", csv_path, row_count)
        return _source()

    def run_pipeline(self, pipeline: Pipeline, source: Any) -> int:
        """
        Run the full Extract → Normalize → Load sequence and verify each step.

        Row counts are only available after normalize(), not after extract(),
        so the emptiness check is performed at that stage.

        Args:
            pipeline: an initialised dlt.pipeline object.
            source:   the final DLT resource/pipe to load (source_resource | transformer).

        Returns:
            Total number of rows loaded.

        Raises:
            ValueError: if normalize produces 0 rows.
            Exception:  propagates any failed Salesforce load jobs.
        """
        pipeline.extract(source)

        normalize_info = pipeline.normalize()
        row_counts = normalize_info.row_counts if hasattr(normalize_info, "row_counts") else {}
        total_rows = sum(row_counts.values())

        if total_rows == 0:
            raise ValueError(
                f"Normalize produced 0 rows for pipeline '{self.pipeline_name}'. "
                "The transformer may have yielded nothing. Aborting."
            )

        pipeline.load().raise_on_failed_jobs()

        self.logger.info(
            "Pipeline '%s' completed — %d row(s) loaded.",
            self.pipeline_name,
            total_rows,
        )

        return total_rows

    def run(self) -> None:
        """Standard execution wrapper with logging and consistent exit codes."""
        try:
            self.logger.info("🚀 Pipeline '%s' starting.", self.pipeline_name)
            self.execute()
            self.logger.info("✅ Pipeline '%s' completed successfully.", self.pipeline_name)
        except Exception as e:
            self.logger.error("❌ Pipeline failed: %s", e)
            import traceback

            traceback.print_exc()
            sys.exit(1)

    @classmethod
    def main(
        cls,
        pipeline_base_name: str,
        default_csv_path: str | None = None,
        default_verbose: bool = True,
    ):
        """Standardized entry point for all pipeline scripts."""
        pipeline = cls(
            pipeline_base_name=pipeline_base_name,
            default_csv_path=default_csv_path,
            verbose=default_verbose,
        )
        pipeline.run()

    # --- 4. ABSTRACT METHODS (To be implemented by subclasses) ---
    @abstractmethod
    def execute(self) -> None:
        """The core pipeline logic. Must be implemented by the subclass."""
        pass

    def add_custom_arguments(self, parser: argparse.ArgumentParser) -> None:  # noqa B027
        """Override in subclasses to add specific CLI arguments."""
        pass

    # --- 5. PRIVATE METHODS (Internal logic) ---
    @staticmethod
    def _setup_logging() -> None:
        """
        Configure the root logger once for the entire process.

        - INFO+ for pipeline code (this module and subclasses)
        - WARNING+ for dlt internals (suppresses extract/normalize chatter
          and urllib3 telemetry calls)
        - DLT’s own handlers are removed so every logger propagates to the
          root handler, producing a unified format across all output
        - force=True ensures this takes effect even when a parent process has
          already attached handlers
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stdout,
            force=True,
        )
        # Remove DLT's own handlers so all output flows through the root
        # handler above, giving a unified format across all loggers.
        dlt_logger = logging.getLogger("dlt")
        dlt_logger.handlers.clear()
        dlt_logger.propagate = True
        dlt_logger.setLevel(logging.WARNING)

    def _setup_and_parse_args(self, default_verbose: bool = True) -> argparse.Namespace:
        """Configures the ArgumentParser with environment, CSV path, and verbose flag."""
        parser = argparse.ArgumentParser(
            description=f"Stairway to Salesforce - {self.pipeline_base_name}",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--env",
            required=False,
            default="dev",
            help="Salesforce environment identifier (default: dev)",
        )

        parser.add_argument(
            "--csv_file",
            default=self.default_csv_path,
            help=f"Path to the source CSV file (default: {self.default_csv_path})",
        )

        parser.add_argument(
            "--verbose",
            action=argparse.BooleanOptionalAction,  # supports --verbose / --no-verbose
            default=default_verbose,
            help="Enable or disable INFO log output (default: True)",
        )

        self.add_custom_arguments(parser)
        return parser.parse_args()
