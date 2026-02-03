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

Enjoy!

### PDF Generation Utility
If automatic PDF generation fails or you need to convert an existing HTML report manually, use the included helper script:
```bash
python convert_to_pdf.py your_report.html
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
