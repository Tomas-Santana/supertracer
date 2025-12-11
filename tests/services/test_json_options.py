import pytest
import json
import os
from supertracer.services.json_options import JSONOptionsService
from supertracer.types.options import SupertracerOptions

class TestJSONOptionsService:
    def test_load_from_file_not_exists(self):
        options = JSONOptionsService.load_from_file("non_existent_file.json")
        assert options is None

    def test_load_from_file_valid(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_data = {
            "logger_options": {"level": 10},
            "metrics_options": {"enabled": False}
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)
            
        options = JSONOptionsService.load_from_file(str(config_file))
        assert isinstance(options, SupertracerOptions)
        assert options.logger_options.level == 10
        assert options.metrics_options.enabled is False

    def test_load_from_file_invalid_json(self, tmp_path):
        config_file = tmp_path / "invalid.json"
        with open(config_file, "w") as f:
            f.write("{invalid_json")
            
        with pytest.raises(ValueError, match="Invalid JSON"):
            JSONOptionsService.load_from_file(str(config_file))

    def test_load_from_file_invalid_config(self, tmp_path):
        config_file = tmp_path / "invalid_config.json"
        config_data = {
            "logger_options": {"level": -1}
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)
            
        with pytest.raises(ValueError, match="Invalid configuration"):
            JSONOptionsService.load_from_file(str(config_file))
