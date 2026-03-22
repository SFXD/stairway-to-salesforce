import argparse
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any

import dlt


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
    ):
        self.pipeline_base_name = pipeline_base_name
        self.default_csv_path = default_csv_path
        self.logger = logging.getLogger(__name__)

        # Parse CLI arguments first
        self.args = self._setup_and_parse_args()

        # Set naming and environment
        self.env: str = self.args.env or self.default_env
        self.pipeline_name = f"{self.pipeline_base_name}_{self.env}"

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
        Get the validated path to the CSV file.
        Raises ValueError if no path was provided, ensuring a 'str' return type for Mypy.
        """
        if not self._csv_file_path or not isinstance(self._csv_file_path, str):
            raise ValueError(
                f"Pipeline '{self.pipeline_name}' requires a CSV file path, "
                "but none was provided via CLI arguments or default configuration."
            )
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

    def run(self) -> None:
        """Standard execution wrapper with logging and consistent exit codes."""
        try:
            self.logger.info(f"🚀 Initializing pipeline: {self.pipeline_name}")
            self.execute()
            self.logger.info(f"✅ Pipeline {self.pipeline_name} completed successfully.")
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    @classmethod
    def main(
        cls,
        pipeline_base_name: str,
        default_csv_path: str | None = None,
    ):
        """Standardized entry point for all pipeline scripts."""
        pipeline = cls(
            pipeline_base_name=pipeline_base_name,
            default_csv_path=default_csv_path,
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
    def _setup_and_parse_args(self) -> argparse.Namespace:
        """Configures the ArgumentParser with environment and optional CSV support."""
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
            help=f"Path to the source CSV File (default: {self.default_csv_path})",
        )

        self.add_custom_arguments(parser)
        return parser.parse_args()
