import json
from pathlib import Path
import os
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    try:
        config_path = Path("config.json")
        if not config_path.exists():
            # Create default config if it doesn't exist
            default_config = {
                "project_root": str(Path.cwd()),
                "wake_word": "hey assistant",
                "log_level": "INFO",
                "deployment": {
                    "environment": "development"
                }
            }
            
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=4)
            
            return default_config
            
        with open(config_path) as f:
            return json.load(f)
            
    except Exception as e:
        raise Exception(f"Error loading configuration: {e}")