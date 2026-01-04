import sys
import os
try:
    from weasyprint import HTML
except OSError:
    print("Error: WeasyPrint (GTK) not found. Cannot generate PDF.")
    sys.exit(1)
except ImportError:
    print("Error: WeasyPrint not installed. Run: pip install weasyprint")
    sys.exit(1)

def convert_html_to_pdf(html_path):
    if not os.path.exists(html_path):
        print(f"Error: File not found: {html_path}")
        return

    output_path = html_path.replace(".html", ".pdf")
    print(f"Converting {html_path} to {output_path}...")
    
    try:
        HTML(filename=html_path).write_pdf(output_path)
        print("Success! PDF generated.")
    except Exception as e:
        print(f"Conversion failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_to_pdf.py <report.html>")
    else:
        convert_html_to_pdf(sys.argv[1])
