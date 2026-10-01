import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

ARTEFACTS_DIR = os.getenv("ARTEFACTS_DIR", "./artefacts")
METADATA_FILE = os.path.join(ARTEFACTS_DIR, "service_metadata.yaml")


def get_service_metadata(service_name: str, _force_malformed: bool = False) -> Dict[str, Any]:
    """Retrieve metadata for the specified service."""

    if _force_malformed:
        return {
            "error": True,
            "error_code": "MALFORMED_METADATA",
            "message": "Service metadata file is malformed and cannot be parsed.",
        }

    if not os.path.exists(METADATA_FILE):
        return {
            "error": True,
            "error_code": "SERVICE_NOT_FOUND",
            "message": f"Metadata file not found at {METADATA_FILE}.",
        }

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            all_metadata = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return {
            "error": True,
            "error_code": "MALFORMED_METADATA",
            "message": f"Failed to parse service metadata YAML: {e}",
        }

    if not all_metadata or service_name not in all_metadata:
        return {
            "error": True,
            "error_code": "SERVICE_NOT_FOUND",
            "message": f"No metadata found for service '{service_name}'.",
        }

    metadata = all_metadata[service_name]
    metadata["name"] = service_name
    return {"error": False, "metadata": metadata}
