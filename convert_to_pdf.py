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
        # Read content to inject strict CSS for PDF compatibility
        # This fixes issues even for reports generated with older templates
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Fix: Inject strict CSS to force word wrapping and fixed layout
        css_patch = """
        <style>
            table { table-layout: fixed !important; width: 100% !important; }
            td, th { 
                word-wrap: break-word !important; 
                overflow-wrap: anywhere !important; 
                word-break: break-all !important; 
                white-space: pre-wrap !important;
                max-width: 100%;
            }
            .scrollable-cell { 
                max-height: none !important; 
                overflow: visible !important; 
                display: block !important;
            }
            @media print {
                tr { page-break-inside: avoid; }
            }
        </style>
        """
        html_content = html_content.replace("</head>", css_patch + "</head>")

        HTML(string=html_content).write_pdf(output_path)
        print("Success! PDF generated.")
    except Exception as e:
        print(f"Conversion failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_to_pdf.py <report.html>")
    else:
        convert_html_to_pdf(sys.argv[1])
