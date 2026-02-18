import argparse
import sys
import logging
import dlt
from abc import ABC, abstractmethod
from typing import Optional

class BasePipeline(ABC):
    """
    Standardized base class for the Stairway to Salesforce project.
    Handles CLI arguments, logging, Salesforce credential routing, 
    and optional CSV file path management.
    """
    def __init__(
        self, 
        pipeline_base_name: str, 
        default_csv_path: Optional[str] = None,
        default_env: Optional[str] = None
    ):
        self.pipeline_base_name = pipeline_base_name
        self.default_csv_path = default_csv_path
        self.default_env = default_env
        self.logger = logging.getLogger(__name__)
        
        # 1. Setup and parse arguments
        self.args = self._setup_and_parse_args()
        
        # 2. Extract environment and set standard naming
        self.env = self.args.env
        self.pipeline_name = f"{self.pipeline_base_name}_{self.env}"
        
        # 3. Salesforce-specific variables (Standardized naming)
        self.sf_credential_path = f"salesforce.{self.env}"
        
        # 4. CSV-specific variables
        # Safely extract from args or fallback to default
        self.csv_file_path = getattr(self.args, "csv_file", default_csv_path)

    def _setup_and_parse_args(self) -> argparse.Namespace:
        """
        Configures the ArgumentParser with environment and optional CSV support.
        """
        parser = argparse.ArgumentParser(
            description=f"Stairway to Salesforce - {self.pipeline_base_name}",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Environment argument - Mandatory unless a default_env is provided
        parser.add_argument(
            '--env', 
            required=self.default_env is None,
            default=self.default_env,
            help=f"Salesforce environment identifier (default: {self.default_env})"
        )
        
        # Optional CSV path argument
        parser.add_argument(
            '--csv_file', 
            default=self.default_csv_path, 
            help=f"Path to the source CSV File (default: {self.default_csv_path})"
        )

        # HOOK: Allow subclasses to add or override specific arguments
        self.add_custom_arguments(parser)
        
        return parser.parse_args()
    
    def add_custom_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Override this method in subclasses to add specific CLI arguments.
        Example: parser.add_argument('--limit', type=int)
        """
        pass    

    def get_credentials(self, basepath : str):
        credential_path = f"{basepath}.{self.env}"
        return dlt.secrets[credential_path] 

    @abstractmethod
    def execute(self) -> None:
        """
        The core pipeline logic (DLT source, hints, and run). 
        Must be implemented by the subclass.
        """
        pass

    def run(self) -> None:
        """
        Standard execution wrapper with logging and consistent exit codes.
        """
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
        default_csv_path: Optional[str] = None,
        default_env: Optional[str] = None
    ):
        """
        Standardized entry point for all pipeline scripts.
        """
        pipeline = cls(
            pipeline_base_name=pipeline_base_name, 
            default_csv_path=default_csv_path,
            default_env=default_env
        )
        pipeline.run()


