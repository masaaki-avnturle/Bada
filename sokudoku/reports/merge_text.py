import PyPDF2

def merge_pdfs(output_file, input_files):
    pdf_writer = PyPDF2.PdfWriter()

    for input_file in input_files:
        pdf_reader = PyPDF2.PdfReader(input_file)
        num_pages = len(pdf_reader.pages)

        for page in range(num_pages):
            pdf_writer.add_page(pdf_reader.pages[page])

    total_pages = len(pdf_writer.pages)
    for i in range(total_pages):
        page = pdf_writer.pages[i]
        page.merge_page(create_page_number_page(i + 1, total_pages))

    with open(output_file, 'wb') as out_file:
        pdf_writer.write(out_file)

def create_page_number_page(page_number, total_pages):
    from PyPDF2 import PdfWriter, PdfReader
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    import io

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    can.drawString(500, 10, "{page_number}/{total_pages}")
    can.save()

    packet.seek(0)
    new_pdf = PdfReader(packet)
    
    return new_pdf.pages[0]

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python merge_pdfs.py output.pdf input1.pdf input2.pdf [...]")
        sys.exit(1)

    output_file = sys.argv[1]
    input_files = sys.argv[2:]

    merge_pdfs(output_file, input_files)
