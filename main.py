import os
import json
from typing import List, Dict, Any
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from functools import partial

# Inspect AL imports
from inspect_ai import eval as inspect_eval
from inspect_ai.log import EvalLog

# Local imports
from config import Config
from tasks.security import run_garak_scan, parse_garak_report
from tasks.evals import safeguards_refusal, trust_privacy, accuracy_hallucination, fairness_bias, toxicity_check
from reporter import Reporter

HISTORY_FILE = "scan_history.json"

console = Console()

def load_history() -> Dict[str, Any]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_history(history: Dict[str, Any]):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

def run_security_phase(model_name: str, skip_if_done: bool = False, history: Dict = None) -> Dict[str, Any]:
    """Phase 1: Security Scanning with Garak"""
    console.print(Panel("[bold red]Phase 1: Security Scanning (Garak)[/bold red]", border_style="red"))
    
    if skip_if_done and history and history.get(model_name, {}).get("security_done"):
        console.print("[yellow]Skipping Security Phase (Already Completed)[/yellow]")
        return history[model_name]["security_results"]

    # Run Garak in a way that we can show progress or just wait
    # Since it's a subprocess, we just wait.
    run_garak_scan(model_name)
    
    # Parse results
    results = parse_garak_report()
    console.print(f"Garak Scan Complete. Attack Success Rate: [bold]{results['attack_success_rate']:.2f}%[/bold]")
    return results

def run_compliance_phase(model_name: str, skip_if_done: bool = False, history: Dict = None) -> Dict[str, Any]:
    """Phase 2: Compliance & Safety with Inspect AI"""
    console.print(Panel("[bold blue]Phase 2: Compliance & Safety (Inspect AI)[/bold blue]", border_style="blue"))
    

    # Initialize history structure for this model if strictly needed here, 
    # but passed 'history' dict should be mutable and persist.
    
    if "compliance_tasks" not in history.get(model_name, {}):
        if model_name not in history: history[model_name] = {}
        if "compliance_tasks" not in history[model_name]: history[model_name]["compliance_tasks"] = {}

    # Use native 'ollama' provider for the Target to isolate it from the 'openai' provider used for the Judge
    # This ensures that setting OPENAI_BASE_URL for HF doesn't break the local target connection.
    inspect_model = f"ollama/{model_name}"
    
    # Configure 'openai' provider to point to Hugging Face for the Judge
    if Config.HF_TOKEN:
        os.environ["OPENAI_API_KEY"] = Config.HF_TOKEN
        # Hugging Face Router compatible endpoint
        os.environ["OPENAI_BASE_URL"] = "https://router.huggingface.co/v1/"
        console.print(f"[dim]Configured OpenAI provider for Cloud Judge (HF Router)[/dim]")
    else:
        # If no HF token, ensure OpenAI vars don't point to nowhere or old values
        # though we really shouldn't use openai provider in this case.
        if "OPENAI_BASE_URL" in os.environ:
            del os.environ["OPENAI_BASE_URL"]
    
    results = {}
    
    # Run Tasks sequentially
    tasks = [
        ("Safeguards (Refusal)", safeguards_refusal, "safeguards_refusal"),
        ("Trust (Privacy)", trust_privacy, "trust_privacy"),
        ("Accuracy (Hallucination)", accuracy_hallucination, "accuracy_hallucination"),
        ("Fairness (Bias)", fairness_bias, "fairness_bias"),
        ("Safety (Toxicity)", toxicity_check, "toxicity_check")
    ]

    for human_name, task_func, task_key in tasks:
        # Check if task is already done
        cached_task = history[model_name]["compliance_tasks"].get(task_key)
        
        if skip_if_done and cached_task and cached_task.get("status") == "completed":
             console.print(f"[yellow]Skipping {human_name} (Already Completed)[/yellow]")
             # Re-hydrate results for report
             score = cached_task.get("score", 0)
             if "Refusal" in human_name: results["refusal_rate"] = score * 100
             elif "Privacy" in human_name: results["pii_leakage_rate"] = (1.0 - score) * 100
             elif "Accuracy" in human_name: results["accuracy_score"] = score * 100
             
             # Restore details
             results[f"{task_key}_details"] = cached_task.get("details", "")
             continue

        console.print(f"Running Task: [bold]{human_name}[/bold]...")
        # Run eval
        # Note: eval returns a list of logs (one per task)
        logs = inspect_eval(task_func(), model=inspect_model, limit=10) # limit for speed
        
        # Analyze log to get score
        if logs and logs[0].results:
             # logs[0].results.scores is a list of EvalScore objects (one per scorer usually)
             eval_score_obj = logs[0].results.scores[0]
             
             # Evaluate how to get the value.
             # If it has 'metrics' dict (common for EvalScore), use that.
             # If it has 'value' (simple Score), use that.
             score = 0
             metric_name = "unknown"
             
             if hasattr(eval_score_obj, "metrics") and eval_score_obj.metrics:
                 # Take the first metric (usually accuracy)
                 metric_name = list(eval_score_obj.metrics.keys())[0]
                 score = eval_score_obj.metrics[metric_name].value
             elif hasattr(eval_score_obj, "value"):
                 score = eval_score_obj.value
                 metric_name = getattr(eval_score_obj, "name", "score")
             else:
                 # Fallback: Try to print/debug or assume 0
                 console.print(f"[red]Could not parse score object: {dir(eval_score_obj)}[/red]")
                 
             # Convert to percentage or relevant metric
             console.print(f"  -> {metric_name}: {score}")
             
             # Save to results dict for this run return
             if "Refusal" in human_name:
                 results["refusal_rate"] = score * 100
             elif "Privacy" in human_name:
                 results["pii_leakage_rate"] = (1.0 - score) * 100 
             elif "Accuracy" in human_name:
                 results["accuracy_score"] = score * 100
             elif "Fairness" in human_name:
                 results["fairness_score"] = score * 100
             elif "Safety" in human_name: # Toxicity
                 results["toxicity_score"] = score * 100
            
             # --- Detailed Sample Extraction ---
             # We want to capture every interaction for the final report
             if "detailed_samples" not in results:
                 results["detailed_samples"] = []

             current_task_detailed_samples = []

             if logs and logs[0].samples:
                 for sample in logs[0].samples:
                     # Get Score explanation and value
                     sample_score_val = 0.0
                     explanation = "No explanation"
                     
                     if sample.scores:
                         # sample.scores is Dict[scorer_name, Score]
                         for s_name, s_obj in sample.scores.items():
                             sample_score_val = s_obj.value if hasattr(s_obj, "value") else 0.0
                             explanation = s_obj.explanation if hasattr(s_obj, "explanation") else str(s_obj)
                             break # Just take the first one
                     
                     # Determine Pass/Fail for this single sample based on task type
                     # Refusal: 1.0 = PASS
                     # Accuracy: 1.0 = PASS
                     # Privacy: 0.0 = FAIL (Leak) -> Wait. pii_scanner returns 1.0 for Safe, 0.0 for Leak.
                     # So consistently 1.0 is GOOD, 0.0 is BAD.
                     is_pass = (sample_score_val > 0.9)
                     
                     sample_data = {
                         "category": human_name,
                         "input": str(sample.input)[:500], # Truncate if too long
                         "response": str(sample.output.completion)[:500],
                         "judge_decision": explanation,
                         "score": sample_score_val,
                         "status": "PASS" if is_pass else "FAIL"
                     }
                     results["detailed_samples"].append(sample_data)
                     current_task_detailed_samples.append(sample_data)
                     
             # Aggregate unique explanations for summary
             unique_explanations = list(set([s["judge_decision"] for s in current_task_detailed_samples]))[:3]
             details_text = "; ".join(unique_explanations) if unique_explanations else "No details available."

             # Update History Immediately
             history[model_name]["compliance_tasks"][task_key] = {
                 "status": "completed",
                 "score": score,
                 "metric": metric_name,
                 "details": details_text,
                 "samples_count": len(logs[0].samples),
                 "samples": current_task_detailed_samples # Store samples for this task in history
             }
             save_history(history)
             
             # Save summary details to results
             results[f"{task_key}_details"] = details_text

        else:
             console.print(f"  -> [yellow]No results found[/yellow]")

    return results

def main():
    console.print(Panel.fit("[bold green]LocalGuard[/bold green]\nAI Safety Auditor", border_style="green"))
    
    # Debug Config
    Config.validate()
    if Config.HF_TOKEN:
        console.print("[green]HF_TOKEN detected. Cloud Judge enabled.[/green]")
    else:
        console.print("[yellow]HF_TOKEN not found. Using Local Judge.[/yellow]")

    # 1. Get Model Name
    default_model = "llama3.1:8b"
    model_name = Prompt.ask("Enter Ollama Model Name", default=default_model)
    
    # Data collection to hold all results
    combined_results = {
        "model_name": model_name,
        "failures": [] # We need to populate this from logs if possible
    }
    
    # 2. Run Phases
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Phase 1: Security
        # We process visually outside the spinner for Garak since it prints to stdout? 
        # Actually Garak prints a lot. Let's run it.
        pass # Just start

    # Run Phases
    history = load_history()

    # Running Garak (Synchronous/Subprocess)
    sec_results = run_security_phase(model_name, skip_if_done=True, history=history)
    combined_results["garak_asr"] = sec_results.get("attack_success_rate", 0)
    # Append Garak failures to general detailed log
    if "failures" in sec_results:
        for f in sec_results["failures"]:
            combined_results["failures"].append(f)
    
    # Phase 2: Compliance
    # Inspect AI eval handles its own async loop internally
    comp_results = run_compliance_phase(model_name, skip_if_done=True, history=history)
    combined_results.update(comp_results)
    
    # Merge detailed samples into a master list for the report
    if "detailed_samples" in comp_results:
        # We can treat Inspect samples as "failures" if they failed, or just a separate list.
        # The user wants "details of what test we have run what passed what failed".
        # So we should pass ALL samples.
        combined_results["all_tests"] = combined_results.get("failures", []) + comp_results["detailed_samples"]
    else:
        combined_results["all_tests"] = combined_results.get("failures", [])
    
    
    # Update History for Security (Done in one block for now)
    if model_name not in history:
        history[model_name] = {}
        
    if sec_results:
        history[model_name]["security_done"] = True
        history[model_name]["security_results"] = sec_results
        save_history(history)
    
    # Note: Compliance history is updated inside the function task-by-task.
        
    # Phase 3: Reporting
    
    # Phase 3: Reporting
    console.print(Panel("[bold magenta]Phase 3: Generating Report[/bold magenta]", border_style="magenta"))
    reporter = Reporter()
    # Normalize filename for report
    safe_model_name = model_name.replace(":", "_").replace("/", "_")
    report_filename = f"LocalGuard_Report_{safe_model_name}.pdf"
    
    final_path = reporter.generate_report(combined_results, report_filename)
    console.print(f"[bold green]Audit Complete! Report saved to: {final_path}[/bold green]")

if __name__ == "__main__":
    main()
