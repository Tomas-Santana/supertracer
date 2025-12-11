import json
import os
from typing import Optional
from supertracer.types.options import SupertracerOptions
import logging

logger = logging.getLogger(__name__)

class JSONOptionsService:
    @staticmethod
    def load_from_file(file_path: str = "supertracer.config.json") -> Optional[SupertracerOptions]:
        """
        Loads SupertracerOptions from a JSON file.
        
        Args:
            file_path: Path to the JSON configuration file.
            
        Returns:
            SupertracerOptions object if file exists and is valid, None if file does not exist.
            
        Raises:
            ValueError: If the file exists but contains invalid configuration.
        """
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Pydantic will handle validation and type coercion
            return SupertracerOptions(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Invalid configuration in {file_path}: {e}")
