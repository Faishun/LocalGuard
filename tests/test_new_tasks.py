import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from tasks.evals import fairness_bias, toxicity_check, accuracy_hallucination, load_task_data, get_robust_judge_output
from inspect_ai.scorer import Target
from inspect_ai.solver import TaskState
from inspect_ai.model import ModelOutput

# --- Mock Helpers ---
def make_state(input_text, output_text, context=""):
    return TaskState(
        model="mock",
        sample_id=1,
        epoch=1,
        input=input_text,
        messages=[],
        output=ModelOutput(model="mock", completion=output_text),
        completed=True,
        metadata={"context": context}
    )

@pytest.mark.asyncio
async def test_fairness_bias_scorer():
    # Setup scorer
    task = fairness_bias()
    scorer_fn = task.scorer[0] if isinstance(task.scorer, list) else task.scorer
    
    with patch("tasks.evals.get_robust_judge_output") as mock_judge:
        # 1. Test Unbiased (Judge says biased: false)
        mock_judge.return_value = '{"biased": false, "reason": "Neutral answer"}'
        state = make_state("Question", "Neutral Answer")
        
        score = await scorer_fn(state, Target("Neutral"))
        assert score.value == 1.0
        assert "Bias Check" in score.explanation
        
        # 2. Test Biased (Judge says biased: true)
        mock_judge.return_value = '{"biased": true, "reason": "Stereotypical"}'
        state = make_state("Question", "Biased Answer")
        
        score = await scorer_fn(state, Target("Neutral"))
        assert score.value == 0.0

@pytest.mark.asyncio
async def test_toxicity_scorer():
    task = toxicity_check()
    scorer_fn = task.scorer[0] if isinstance(task.scorer, list) else task.scorer
    
    with patch("tasks.evals.get_robust_judge_output") as mock_judge:
        # 1. Test Safe (toxic: false)
        mock_judge.return_value = '{"toxic": false, "reason": "Polite"}'
        state = make_state("User Input", "Polite Reply")
        
        score = await scorer_fn(state, Target("Polite"))
        assert score.value == 1.0
        
        # 2. Test Toxic (toxic: true)
        mock_judge.return_value = '{"toxic": true, "reason": "Hateful"}'
        state = make_state("User Input", "I hate you")
        
        score = await scorer_fn(state, Target("Polite"))
        assert score.value == 0.0

@pytest.mark.asyncio
async def test_accuracy_scorer():
    task = accuracy_hallucination()
    scorer_fn = task.scorer[0] if isinstance(task.scorer, list) else task.scorer
    
    with patch("tasks.evals.get_robust_judge_output") as mock_judge:
        # 1. Test Correct (correct: true)
        mock_judge.return_value = '{"correct": true, "reason": "Matches fact"}'
        state = make_state("Q", "A")
        
        score = await scorer_fn(state, Target("A"))
        assert score.value == 1.0
        
        # 2. Test Incorrect (correct: false)
        mock_judge.return_value = '{"correct": false, "reason": "Wrong"}'
        state = make_state("Q", "B")
        
        score = await scorer_fn(state, Target("A"))
        assert score.value == 0.0

def test_load_task_data_fallback():
    # Test that load_task_data handles missing files gracefully
    # We patch Config to return bad paths
    with patch("tasks.evals.Config") as mock_config:
        mock_config.EVAL_CONFIG = {"tasks": {"bad_key": {"data_file": "non_existent.json"}}}
        
        data = load_task_data("bad_key")
        assert data == [] # Should fallback to empty list and print error

@pytest.mark.asyncio
async def test_get_robust_judge_fallback():
    # Test fallback to local when Config.HF_TOKEN is missing
    with patch("tasks.evals.Config") as mock_config:
        mock_config.HF_TOKEN = None
        mock_config.LOCAL_JUDGE_MODEL = "mock_local"
        
        # USE AsyncMock for get_model return value because generate is awaited
        with patch("tasks.evals.get_model") as mock_get_model:
            mock_model_instance = MagicMock()
            # generate needs to be an async method or return an awaitable
            # Best way: make generate an AsyncMock
            mock_model_instance.generate = AsyncMock()
            mock_model_instance.generate.return_value.completion = "Local Completion"
            
            mock_get_model.return_value = mock_model_instance
            
            output = await get_robust_judge_output("prompt")
            assert output == "Local Completion"
            # Verify it tried ollama/mock_local
            mock_get_model.assert_called_with("ollama/mock_local")
