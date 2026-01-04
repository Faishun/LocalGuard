import subprocess
import json
import os
from typing import Dict, Any

def run_garak_scan(target_model_name: str, report_prefix: str = "garak_out") -> None:
    """
    Runs Garak security scanner against the specified Ollama model.
    Results are saved to the default Garak report directory or local.
    """
    # Verify Ollama is reachable is implicit, Garak handles connection errors usually.
    
    import sys
    from config import Config
    
    # Use 'litellm' generator which handles Ollama robustly via 'ollama/model'
    # This avoids Garak's internal OpenAI whitelist issues.
    command = [
        sys.executable, "-m", "garak",
        "--model_type", "litellm",
        "--model_name", f"ollama/{target_model_name}",
        "--probes", "dan,promptinject",
        "--report_prefix", report_prefix,
        "--generations", "5" 
    ]
    
    # Pass environment variables to the subprocess to configure OpenAI base URL
    env = os.environ.copy()
    env["OPENAI_API_BASE"] = Config.OLLAMA_URL
    env["OPENAI_API_KEY"] = Config.OLLAMA_API_KEY
    
    print(f"Starting Garak scan on {target_model_name} (via OpenAI Interface)...")
    try:
        # Check if garak is installed (it should be)
        # Check if garak is installed (it should be)
        subprocess.run(command, check=True, env=env)
        print("Garak scan completed.")
    except subprocess.CalledProcessError as e:
        print(f"Error running Garak: {e}")
    except FileNotFoundError:
        print("Error: 'garak' command not found. Please ensure it is installed.")

def parse_garak_report(report_path: str = "garak_out.report.jsonl") -> Dict[str, Any]:
    """
    Parses the Garak JSONL report to calculate Attack Success Rate.
    Searches for the report in CWD and Garak default directories.
    """
    # Search logic for the report file
    candidates = [report_path]
    
    # Check default Garak directories (Linux/Mac/Windows .local style)
    from pathlib import Path
    home = Path.home()
    # Common locations for Garak output
    garak_dirs = [
        home / ".local" / "share" / "garak" / "garak_runs",
        home / "AppData" / "Local" / "garak" / "garak_runs"
    ]
    
    for d in garak_dirs:
        if d.exists():
            # Find files matching the prefix, sorted by mtime (newest first)
            found = list(d.glob(f"garak_out*.report.jsonl"))
            found.sort(key=os.path.getmtime, reverse=True)
            if found:
                candidates.extend([str(f) for f in found])

    final_report_path = None
    for p in candidates:
        if os.path.exists(p):
            final_report_path = p
            break
            
    if not final_report_path:
        print(f"[Warning] Garak report not found. Searched: {candidates[:1]} and standard dirs.")
        return {"error": "Report file not found", "attack_success_rate": 0.0}
    
    print(f"Parsing Garak report: {final_report_path}")

    total_attempts = 0
    successful_attacks = 0
    
    with open(final_report_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                # Garak report structure varies, but generally 'entry_type' indicates what log it is.
                # We start simple. Look for evaluation results.
                # Typically entry_type="eval" contains 'status'.
                
                if record.get("entry_type") == "eval":
                    total_attempts += 1
                    # Status 'fail' usually means the model FAILED the safety check (i.e. Attack SUCCEEDED)
                    # Wait, Garak terminology:
                    # Pass = Model defended itself
                    # Fail = Model failed to defend (Vulnerable)
                    if record.get("status") == "fail": 
                        successful_attacks += 1
                        
            except json.JSONDecodeError:
                continue

    attack_success_rate = (successful_attacks / total_attempts * 100) if total_attempts > 0 else 0.0
    
    return {
        "total_attempts": total_attempts,
        "successful_attacks": successful_attacks,
        "attack_success_rate": attack_success_rate
    }
