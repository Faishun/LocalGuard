# LocalGuard: AI Safety Audit Tool

LocalGuard is a comprehensive, local-first safety auditing tool for Large Language Models (LLMs). It integrates industry-standard frameworks to evaluate models for security vulnerabilities, compliance with safety guidelines, and performance reliability.

Example report (HTML): [LocalGuard_Report_gemma3_4b.html](LocalGuard_Report_gemma3_4b.pdf) — a sample audit report generated for the gemma3_4b model.

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
*   **Multi-Provider Support**: 
    *   **Local**: Ollama, vLLM, LM Studio (OpenAI Compatible).
    *   **Cloud**: OpenAI (GPT-4), Anthropic (Claude), Google (Gemini), Hugging Face (Inference API).
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
*   **GTK3 Runtime** (Required for PDF Generation on Windows):
    *   Download and install from [latest releases](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases).
    *   **Restart your terminal/IDE** after installation.
    *   *Note: If missing, reports will be generated as HTML.*

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
    # Hugging Face Token (Required for HF Provider & Cloud Judge)
    HF_TOKEN=hf_your_token_here
    
    # Cloud Provider Keys (If using specific providers)
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
    GOOGLE_API_KEY=...
    
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

1.  **Select Provider**: Choose from Ollama, OpenAI, Anthropic, Google, Hugging Face, etc.
2.  **Enter Model**: Input the model name (e.g., `gpt-4o`, `meta-llama/Meta-Llama-3-8B-Instruct`).
3.  **Monitor Progress**: The tool will run the Security Phase (Garak) followed by the Compliance Phase (Inspect AI).
4.  **View Report**: Upon completion, a report (e.g., `LocalGuard_Report_gpt-4o.pdf`) will be generated.

### PDF Generation Utility
If automatic PDF generation fails or you need to convert an existing HTML report manually, use the included helper script:
```bash
python convert_to_pdf.py your_report.html
```

LocalGuard orchestrates two powerful libraries:

1.  **Garak**: Performs proactive "attacks" on the model to find security holes.
2.  **Inspect AI**: Runs structured evaluation tasks where the model's responses are graded by a "Judge" model.

The **Orchestrator** (`main.py`) manages the workflow, handles data passing, manages state (`scan_history.json`), and compiles the final report (`reporter.py`).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
