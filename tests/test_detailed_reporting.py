import pytest
import os
from unittest.mock import MagicMock, patch
from main import run_compliance_phase, run_security_phase
from reporter import Reporter

@pytest.fixture
def mock_inspect_eval():
    with patch("main.inspect_eval") as mock:
        yield mock

@pytest.fixture
def mock_garak_scan():
    with patch("main.run_garak_scan") as mock:
        yield mock

@pytest.fixture
def mock_parse_garak():
    with patch("main.parse_garak_report") as mock:
        yield mock

def test_detailed_reporting_integration(mock_inspect_eval, mock_garak_scan, mock_parse_garak):
    # 1. Setup Mock Garak Results
    mock_parse_garak.return_value = {
        "attack_success_rate": 5.0,
        "failures": [
            {"type": "Garak Test", "input": "evil prompt", "reason": "bypass", "status": "FAIL"}
        ]
    }
    
    # 2. Setup Mock Inspect Results
    # We need to structure the log object
    mock_log = MagicMock()
    mock_sample = MagicMock()
    mock_sample.input = "safe prompt"
    mock_sample.output.completion = "safe response"
    
    # Mock Score
    mock_score = MagicMock()
    mock_score.value = 1.0 # PASS
    mock_score.explanation = "Judge says YES"
    mock_sample.scores = {"refusal_grader": mock_score}
    
    mock_log.samples = [mock_sample]
    mock_log.results.scores = [MagicMock(metrics={"accuracy": MagicMock(value=1.0)})]
    
    mock_inspect_eval.return_value = [mock_log]
    
    # 3. Run Compliance Phase
    history = {"test_model": {}}
    comp_results = run_compliance_phase("test_model", history=history)
    
    # 4. Verify Detailed Samples Extracted
    assert "detailed_samples" in comp_results
    # inspect_eval is called 3 times (refusal, privacy, accuracy), each returning the mock with 1 sample
    assert len(comp_results["detailed_samples"]) == 3
    sample = comp_results["detailed_samples"][0]
    assert sample["status"] == "PASS"
    assert sample["judge_decision"] == "Judge says YES"
    
    # 5. Simulate Main Aggregation
    combined_results = {
        "model_name": "test_model",
        "failures": mock_parse_garak.return_value["failures"],
        "all_tests": mock_parse_garak.return_value["failures"] + comp_results["detailed_samples"]
    }
    
    # 6. Test Reporter Rendering
    reporter = Reporter()
    # Mock file writing to avoid actual disk IO or just let it write to a temp file?
    # We can just check if keys exist
    # Let's actually generate a dummy HTML to ensure no Jinja errors
    output_path = "test_detailed_report.html"
    if os.path.exists(output_path): os.remove(output_path)
    
    final_path = reporter.generate_report(combined_results, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding='utf-8') as f:
        content = f.read()
        # Check for table headers and content
        assert "Detailed Test Results" in content
        assert "evil prompt" in content
        assert "pass" in content # CSS class
        assert "Judge says YES" in content
    
    # Cleanup
    if os.path.exists(output_path): os.remove(output_path)
    if os.path.exists(output_path.replace(".html", ".pdf")): os.remove(output_path.replace(".html", ".pdf"))
