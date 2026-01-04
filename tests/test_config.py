import pytest
from unittest.mock import patch, mock_open
import os
import sys

# Ensure path is set for import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def test_load_eval_config_success():
    yaml_content = """
    evaluator:
      judge_model: "test_judge"
    tasks:
      test_task:
        enabled: true
    """
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        with patch("os.path.exists", return_value=True):
             Config.load_eval_config()
             assert Config.EVAL_CONFIG["evaluator"]["judge_model"] == "test_judge"

def test_load_eval_config_not_found():
    # If file doesn't exist, EVAL_CONFIG remains empty (or previous state)
    Config.EVAL_CONFIG = {}
    with patch("os.path.exists", return_value=False):
        Config.load_eval_config()
        assert Config.EVAL_CONFIG == {}
        
def test_validate_method():
    # Mock load_eval_config to ensure it's called
    with patch.object(Config, "load_eval_config") as mock_load:
        Config.validate()
        assert mock_load.called

