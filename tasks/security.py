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
    # Garak writes to its default run dir (e.g. ~/.local/share/garak/garak_runs/).
    # Prefer that location over CWD so we always use the report from the run we just did.
    from pathlib import Path
    home = Path.home()
    garak_dirs = [
        home / ".local" / "share" / "garak" / "garak_runs",
        home / "AppData" / "Local" / "garak" / "garak_runs"
    ]

    candidates = []
    seen = set()
    for d in garak_dirs:
        if d.exists():
            found = list(d.glob("garak_out*.report.jsonl"))
            found.sort(key=os.path.getmtime, reverse=True)
            for f in found:
                p = str(f)
                if p not in seen:
                    seen.add(p)
                    candidates.append(p)
    # CWD as fallback (e.g. if Garak was run with a custom report path)
    cwd_path = os.path.abspath(report_path)
    if cwd_path not in seen and os.path.exists(report_path):
        candidates.append(cwd_path)

    # Prefer Garak default dir (newest there), then CWD
    final_report_path = candidates[0] if candidates else None
            
    if not final_report_path:
        print("[Warning] Garak report not found. Searched Garak run dirs and CWD.")
        return {"error": "Report file not found", "attack_success_rate": 0.0}
    
    print(f"Parsing Garak report: {final_report_path}")

    total_attempts = 0
    successful_attacks = 0
    failures = []
    
    with open(final_report_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                entry_type = record.get("entry_type")

                # Newer Garak schema (0.13+):
                # {"entry_type":"eval","probe":"...","detector":"...","passed":17,"total":127}
                if entry_type == "eval" and "passed" in record and "total" in record:
                    passed = int(record.get("passed", 0) or 0)
                    total = int(record.get("total", 0) or 0)
                    if total <= 0:
                        continue

                    failed = max(total - passed, 0)
                    total_attempts += total
                    successful_attacks += failed

                    if failed > 0:
                        probe_name = record.get("probe", "Unknown Probe")
                        detector_name = record.get("detector", "Unknown Detector")
                        asr = (failed / total) * 100
                        failures.append({
                            "type": f"Garak Security ({probe_name})",
                            "input": f"Detector: {detector_name}",
                            "response": f"Passed {passed}/{total}",
                            "reason": f"{failed}/{total} attacks succeeded ({asr:.2f}% ASR)",
                            "status": "FAIL"
                        })
                    continue

                # Older schema fallback:
                # {"entry_type":"eval","probe":"...","prompt":"...","status":"fail","output":"..."}
                if entry_type == "eval":
                    total_attempts += 1
                    if str(record.get("status", "")).lower() == "fail":
                        successful_attacks += 1

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
