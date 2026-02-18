from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="LocalGuard non-interactive runner (web/worker friendly).")
    parser.add_argument("--provider", required=True, help="Provider key (e.g. ollama, openai, anthropic, google, huggingface, vllm)")
    parser.add_argument("--model", required=True, help="Model name/id")
    parser.add_argument("--mode", choices=["full", "report-only"], default="full")
    parser.add_argument("--out-dir", required=True, help="Directory to write report + history")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Import LocalGuard's existing orchestrator module and reuse logic.
    import main as localguard_main  # LocalGuard/main.py

    # History file: use shared path from env when set (suite_web cache on), else per-run.
    history_path = os.environ.get("LOCALGUARD_HISTORY_FILE")
    if history_path:
        history_path = Path(history_path).resolve()
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path = str(history_path)
    else:
        history_path = str(out_dir / "scan_history.json")
    localguard_main.HISTORY_FILE = history_path

    model_name = args.model
    provider = args.provider

    if args.mode == "report-only":
        history = localguard_main.load_history_from_file()
        if not history:
            raise SystemExit("No saved scan history found. Run mode=full first.")

        combined_results = localguard_main.build_combined_results_from_history(model_name, history)
        # Optionally re-parse garak report (may be outside out_dir), but keep behavior consistent with main.py.
        garak_parsed = localguard_main.parse_garak_report()
        if "error" not in garak_parsed:
            combined_results["garak_asr"] = garak_parsed.get("attack_success_rate", 0)
            combined_results["failures"] = list(garak_parsed.get("failures", []))
            tasks = history.get(model_name, {}).get("compliance_tasks", {})
            detailed_samples = []
            for task_key in ("safeguards_refusal", "trust_privacy", "accuracy_hallucination", "fairness_bias", "toxicity_check"):
                for s in tasks.get(task_key, {}).get("samples", []):
                    detailed_samples.append(s)
            combined_results["all_tests"] = combined_results.get("failures", []) + detailed_samples

        safe_model_name = model_name.replace(":", "_").replace("/", "_")
        report_filename = f"LocalGuard_Report_{safe_model_name}.pdf"
        reporter = localguard_main.Reporter()
        report_path = reporter.generate_report(combined_results, str(out_dir / report_filename))

        _emit_summary(out_dir, report_path, combined_results)
        return 0

    # Full audit mode
    history = localguard_main.load_history()
    if model_name not in history:
        history[model_name] = {}
    history[model_name]["provider"] = provider
    localguard_main.save_history(history)

    sec_results = localguard_main.run_security_phase(model_name, skip_if_done=True, history=history)

    combined_results = {"model_name": model_name, "failures": []}
    combined_results["garak_asr"] = sec_results.get("attack_success_rate", 0)
    if "failures" in sec_results:
        for f in sec_results["failures"]:
            combined_results["failures"].append(f)

    comp_results = localguard_main.run_compliance_phase(model_name, skip_if_done=True, history=history)
    combined_results.update(comp_results)
    if "detailed_samples" in comp_results:
        combined_results["all_tests"] = combined_results.get("failures", []) + comp_results["detailed_samples"]
    else:
        combined_results["all_tests"] = combined_results.get("failures", [])

    # Persist security summary into history (compliance already persists task-by-task).
    history = localguard_main.load_history()
    if model_name not in history:
        history[model_name] = {}
    history[model_name]["security_done"] = True
    history[model_name]["security_results"] = sec_results
    localguard_main.save_history(history)

    safe_model_name = model_name.replace(":", "_").replace("/", "_")
    report_filename = f"LocalGuard_Report_{safe_model_name}.pdf"
    reporter = localguard_main.Reporter()
    report_path = reporter.generate_report(combined_results, str(out_dir / report_filename))

    _emit_summary(out_dir, report_path, combined_results)
    return 0


def _emit_summary(out_dir: Path, report_path: str, combined_results: dict) -> None:
    summary_path = out_dir / "localguard_summary.json"
    summary_path.write_text(json.dumps({"report_path": report_path, "results": combined_results}, indent=2), encoding="utf-8")
    print(json.dumps({"report_path": report_path, "summary_path": str(summary_path)}, ensure_ascii=True))


if __name__ == "__main__":
    raise SystemExit(main())

