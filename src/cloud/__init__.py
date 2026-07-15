"""Cloud integration layer."""
from src.cloud.azure_integration import build_azure_receipt, config_from_env

__all__ = ["build_azure_receipt", "config_from_env"]
