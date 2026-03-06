from io import BytesIO
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF file provided as bytes.
    Uses pdfminer.six for robust extraction with layout analysis.
    """
    try:
        # Create a file-like object from bytes
        pdf_file = BytesIO(file_bytes)
        # Extract text with layout parameters to preserve reading order better
        laparams = LAParams(detect_vertical=True, all_texts=True)
        text = extract_text(pdf_file, laparams=laparams)
        return text if text else ""
    except Exception as e:
        # Log error or handle gracefully
        print(f"Error parsing PDF: {e}")
        return ""
