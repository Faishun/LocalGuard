# LocalGuard: AI Safety Audit Tool

Official repo (for details): https://github.com/overcrash66/LocalGuard

This fork is aimed to use the LocalGuard with LM Studio multiple local models (Tested Model + Judge) with several patches to hardcoded values.

Enjoy!

## 🏃 Usage

Run the main orchestrator:

```bash
python -m main
```

```bash
Custom / Other
```

Populate the .env from .env.example with **your specific environment.**

If you get

```bash
Segmentation fault
```

from Python after runnig **python -m main,** simply rerun it, since other dependency is installed on the go and might not follow the entire process.

Disable **cache feature by specifying yes when running the main ochestrator.** What does it do? It makes sure that you can rerun the test on the model if the name
is the same, but data is changed.

Enjoy!

### PDF Generation Utility
If automatic PDF generation fails or you need to convert an existing HTML report manually, use the included helper script:
```bash
python convert_to_pdf.py your_report.html
```

## ❯❯❯❯ Increase scanning speed

You might receive a message like this from garak:
<img width="1769" height="73" alt="image" src="https://github.com/user-attachments/assets/289ddcf0-c1d1-4bb4-9883-fc8240163bf9" />

If your models supports it, you can add it in **tasks/security.py:**

```bash
command = [
        sys.executable, "-m", "garak",
        "--probes", "dan,promptinject",
        "--report_prefix", report_prefix,
        "--generations", "5",
        "--parallel_attempts", "16"
    ]
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
