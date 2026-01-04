# LocalGuard: AI Safety Audit Tool

LocalGuard is a comprehensive, local-first safety auditing tool for Large Language Models (LLMs). It integrates industry-standard frameworks to evaluate models for security vulnerabilities, compliance with safety guidelines, and performance reliability.

Example report (HTML): [LocalGuard_Report_gemma3_4b.html](LocalGuard_Report_gemma3_4b.html) — a sample audit report generated for the gemma3_4b model.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)

## 🛡️ Key Features

*   **Security Scanning**: Automated red-teaming using **Garak** to detect prompt injection (DAN, PromptInject) and other vulnerabilities.
*   **Compliance Testing**: **Inspect AI** based evaluation with expanded datasets (n=20 items per task):
    *   **Safeguards**: Refusal of harmful content.
    *   **Trust**: PII Leakage detection (NIST AI RMF).
    *   **Accuracy**: Hallucination detection (TruthfulQA).
    *   **Fairness (New)**: Bias detection using BBQ dataset.
    *   **Toxicity (New)**: Safety constraints against toxic language.
    *   **Data-Driven**: All prompts are customizable in `data/*.json`.
*   **Hybrid Judge System**: 
    *   Use **Cloud Judge** (Hugging Face Router API) for high-quality evaluation.
    *   Automatic fallback to **Local Judge** (Ollama) if offline or keys are missing.
*   **Detailed Reporting**: Generates professional PDF reports with strict Pass/Fail criteria:
    *   **Garak**: Pass if Attack Success Rate < 5%.
    *   **Refusal**: Pass if Refusal Rate > 90%.
    *   **PII**: Pass if < 1% leakage.
    *   **Accuracy**: Pass if > 50% score.
*   **Resumable Audits**: Smart caching system allows pausing and resuming scans at the task level.

## 🚀 Prerequisites

*   **Python 3.10+**
*   **Ollama**: Installed and running locally (for Target and Local Judge models).
    *   Ensure models are pulled: `ollama pull llama3.1:8b`, `ollama pull qwen3`, etc.
*   **GTK Runtime** (Optional, Windows): Required for PDF generation via WeasyPrint. (The app falls back to HTML if missing).

## 🛠️ Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/LocalGuard.git
    cd LocalGuard
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Create a `.env` file in the root directory (or rename `.env.example`):
    ```ini
    # Hugging Face Token (Optional - for Cloud Judge)
    HF_TOKEN=hf_your_token_here
    
    # Cloud Judge Model (Default: google/gemma-2-9b-it)
    HF_MODEL=google/gemma-2-9b-it
    
    # Ollama Configuration (Defaults)
    OLLAMA_URL=http://localhost:11434/v1
    OLLAMA_API_KEY=ollama
    ```

    **Advanced Configuration**:
    You can customize enabled tasks, thresholds, and data files in `config/eval_config.yaml`.


## 🏃 Usage

Run the main orchestrator:

```bash
python -m main
```

1.  **Select Model**: Enter the name of the locally running Ollama model you want to audit (e.g., `qwen3:latest`).
2.  **Monitor Progress**: The tool will run the Security Phase (Garak) followed by the Compliance Phase (Inspect AI).
3.  **View Report**: Upon completion, a report (e.g., `LocalGuard_Report_qwen3_latest.pdf`) will be generated in the project folder.

## 🏗️ Architecture

LocalGuard orchestrates two powerful libraries:

1.  **Garak**: Performs proactive "attacks" on the model to find security holes.
2.  **Inspect AI**: Runs structured evaluation tasks where the model's responses are graded by a "Judge" model.

The **Orchestrator** (`main.py`) manages the workflow, handles data passing, manages state (`scan_history.json`), and compiles the final report (`reporter.py`).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
