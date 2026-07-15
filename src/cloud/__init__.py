"""Cloud integration layer."""
from src.cloud.azure_integration import AzureCognitiveAdapter, build_azure_receipt, config_from_env, send_service_bus_alert

__all__ = ["AzureCognitiveAdapter", "build_azure_receipt", "config_from_env", "send_service_bus_alert"]
