from reportlab.pdfgen import canvas
from io import BytesIO

def create_dummy_pdf():
    c = canvas.Canvas("temp/dummy_pdf.pdf")
    c.drawString(100, 750, "Manuscript limit: 5000 words.")
    c.drawString(100, 730, "Abstract: 250 words max.")
    c.save()

if __name__ == "__main__":
    create_dummy_pdf()
