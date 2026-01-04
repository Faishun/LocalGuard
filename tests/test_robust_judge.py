import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from tasks.evals import get_robust_judge_output
from config import Config

@pytest.fixture
def mock_get_model():
    with patch("tasks.evals.get_model") as mock:
        yield mock

@pytest.mark.asyncio
async def test_robust_judge_all_hf_succeed_first_try(mock_get_model):
    # Setup successful first model
    mock_model_instance = AsyncMock()
    mock_model_instance.generate.return_value.completion = "YES"
    mock_get_model.return_value = mock_model_instance
    
    # Run
    result = await get_robust_judge_output("test prompt")
    
    # Assertions
    assert result == "YES"
    # Should have called get_model with first candidate
    mock_get_model.assert_called_with("openai/" + Config.HF_JUDGE_CANDIDATES[0])

@pytest.mark.asyncio
async def test_robust_judge_fallback_to_second(mock_get_model):
    # Setup: First call raises exception, Second succeeds
    mock_fail = AsyncMock()
    mock_fail.generate.side_effect = Exception("Model Overloaded")
    
    mock_success = AsyncMock()
    mock_success.generate.return_value.completion = "YES"
    
    # We need get_model to return different mocks based on input or sequence
    # Side effect for get_model
    def side_effect(model_name):
        if Config.HF_JUDGE_CANDIDATES[0] in model_name:
            return mock_fail
        return mock_success

    mock_get_model.side_effect = side_effect
    
    # Run
    result = await get_robust_judge_output("test prompt")
    
    assert result == "YES"
    # Should have tried first candidate
    assert mock_fail.generate.called

@pytest.mark.asyncio
async def test_robust_judge_fallback_to_local(mock_get_model):
    # Setup: All HF candidates fail
    mock_fail = AsyncMock()
    mock_fail.generate.side_effect = Exception("Rate Limit")
    
    mock_local = AsyncMock()
    mock_local.generate.return_value.completion = "LOCAL_YES"
    
    def side_effect(model_name):
        if "ollama" in model_name:
            return mock_local
        # All "openai/" calls fail
        return mock_fail

    mock_get_model.side_effect = side_effect
    
    # Run
    result = await get_robust_judge_output("test prompt")
    
    assert result == "LOCAL_YES"
    # Check that we verified local fallback usage
    # get_model should be called with "ollama/qwen3:latest" eventually
    args_list = [call.args[0] for call in mock_get_model.call_args_list]
    assert f"ollama/{Config.LOCAL_JUDGE_MODEL}" in args_list
