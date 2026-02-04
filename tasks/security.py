import subprocess
import json
import os
import importlib.util
from typing import Dict, Any

def run_garak_scan(target_model_name: str, provider: str = "ollama", report_prefix: str = "garak_out") -> bool:
    """
    Runs Garak security scanner against the specified model.
    Results are saved to the default Garak report directory or local.
    """
    import sys
    from config import Config

    def _garak_has_litellm() -> bool:
        return importlib.util.find_spec("garak.generators.litellm") is not None

    def _openai_has_legacy_errors() -> bool:
        try:
            import openai  # type: ignore
            return hasattr(openai, "error")
        except Exception:
            return False
    
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
        # Prefer litellm if garak supports it; otherwise fallback to legacy openai generator.
        if _garak_has_litellm():
            command.extend(["--model_type", "litellm", "--model_name", f"openai/{target_model_name}"])
        elif _openai_has_legacy_errors():
            command.extend(["--model_type", "openai", "--model_name", target_model_name])
        else:
            print("Error: Garak does not have the litellm generator and your OpenAI SDK is v1+.")
            print("Fix: upgrade garak to a version that includes litellm, or pin openai<1.0,")
            print("or use an Ollama provider for security scanning.")
            return False
        # Requires OPENAI_API_KEY in env
        if Config.OPENAI_API_KEY:
            env["OPENAI_API_KEY"] = Config.OPENAI_API_KEY
        # If user set an OpenAI-compatible base (e.g., LM Studio), propagate it
        if "OPENAI_API_BASE" not in env and os.getenv("OPENAI_BASE_URL"):
            env["OPENAI_API_BASE"] = os.getenv("OPENAI_BASE_URL")
        
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
        # Prefer litellm when available, otherwise legacy openai generator
        if _garak_has_litellm():
            command.extend(["--model_type", "litellm", "--model_name", f"openai/{target_model_name}"])
        elif _openai_has_legacy_errors():
            command.extend(["--model_type", "openai", "--model_name", target_model_name])
        else:
            print("Error: Garak does not have the litellm generator and your OpenAI SDK is v1+.")
            print("Fix: upgrade garak to a version that includes litellm, or pin openai<1.0,")
            print("or use an Ollama provider for security scanning.")
            return False
        if Config.OPENAI_API_KEY:
            env["OPENAI_API_KEY"] = Config.OPENAI_API_KEY
        if "OPENAI_API_BASE" not in env and os.getenv("OPENAI_BASE_URL"):
            env["OPENAI_API_BASE"] = os.getenv("OPENAI_BASE_URL")
        
    try:
        subprocess.run(command, check=True, env=env)
        print("Garak scan completed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Garak: {e}")
    except FileNotFoundError:
        print("Error: 'garak' command not found. Please ensure it is installed.")
    return False

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
