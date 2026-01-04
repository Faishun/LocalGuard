import subprocess
import json
import os
from typing import Dict, Any

def run_garak_scan(target_model_name: str, provider: str = "ollama", report_prefix: str = "garak_out") -> None:
    """
    Runs Garak security scanner against the specified model.
    Results are saved to the default Garak report directory or local.
    """
    import sys
    from config import Config
    
    # Base command
    command = [
        sys.executable, "-m", "garak",
        "--probes", "dan,promptinject",
        "--report_prefix", report_prefix,
        "--generations", "5" 
    ]
    
    # Environment Setup
    env = os.environ.copy()
    
    # Logic for Providers
    print(f"Starting Garak scan on {provider}/{target_model_name}...")
    
    if provider == "ollama":
        # Use litellm with 'ollama/' prefix for best results
        command.extend(["--model_type", "litellm", "--model_name", f"ollama/{target_model_name}"])
        env["OPENAI_API_BASE"] = Config.OLLAMA_URL
        env["OPENAI_API_KEY"] = Config.OLLAMA_API_KEY
        
    elif provider == "openai":
        command.extend(["--model_type", "openai", "--model_name", target_model_name])
        # Requires OPENAI_API_KEY in env
        if Config.OPENAI_API_KEY: env["OPENAI_API_KEY"] = Config.OPENAI_API_KEY
        
    elif provider == "anthropic":
        # Garak supports anthropic directly or via litellm
        command.extend(["--model_type", "litellm", "--model_name", f"anthropic/{target_model_name}"])
        if Config.ANTHROPIC_API_KEY: env["ANTHROPIC_API_KEY"] = Config.ANTHROPIC_API_KEY
        
    elif provider == "huggingface":
        # Garak hf support
        command.extend(["--model_type", "huggingface", "--model_name", target_model_name])
        if Config.HF_TOKEN: env["HF_TOKEN"] = Config.HF_TOKEN
        
    elif provider == "google":
        # Garak supports google via litellm/vertex usually
        command.extend(["--model_type", "litellm", "--model_name", f"gemini/{target_model_name}"])
        if Config.GOOGLE_API_KEY: env["GOOGLE_API_KEY"] = Config.GOOGLE_API_KEY
        
    else:
        # Fallback / Custom (assume OpenAI compatible)
        # For vLLM or others, user likely provided full URL in env or we assume defaults
        command.extend(["--model_type", "openai", "--model_name", target_model_name])
        
    try:
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
    failures = []
    
    with open(final_report_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                # Garak report structure:
                # { "entry_type": "eval", "probe": "...", "prompt": "...", "status": "fail", "output": "..." }
                
                if record.get("entry_type") == "eval":
                    total_attempts += 1
                    
                    if record.get("status") == "fail": 
                        successful_attacks += 1
                        
                        # Extract details for the report
                        # Garak structure varies slightly by version, safely get keys
                        probe_name = record.get("probe", "Unknown Probe")
                        prompt_text = record.get("prompt", "N/A")
                        model_output = record.get("output", "N/A")
                        
                        failures.append({
                            "type": f"Garak Security ({probe_name})",
                            "input": prompt_text,
                            "response": model_output,
                            "reason": "Model failed to defend against attack (Safety Filter Bypass)",
                            "status": "FAIL"
                        })
                        
            except json.JSONDecodeError:
                continue

    attack_success_rate = (successful_attacks / total_attempts * 100) if total_attempts > 0 else 0.0
    
    return {
        "total_attempts": total_attempts,
        "successful_attacks": successful_attacks,
        "attack_success_rate": attack_success_rate,
        "failures": failures # Return the list of failures
    }
