import PyPDF2;

def merge_pdfs(output_pdf, input_pdfs):
    pdf_writer = PyPDF2.PdfWriter()

    page_count = 0
    
    for input_pdf in input_pdfs:
        pdf_reader = PyPDF2.PdfReader(input_pdf)
        
        for page in range(len(pdf_reader.pages)):
            page_obj = pdf_reader.pages[page]
            pdf_writer.add_page(page_obj)

	    # ページ番号を設定
            page_number = page_count + 1
            pdf_writer.add_page(PyPDF2.PdfWriter())
            pdf_writer.pages[-1].merge_page(create_page_with_number(page_number))

            page_count += 1

    with open(output_pdf, 'wb') as out:
        pdf_writer.write(out)

def create_page_with_number(page_number):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(500, 10, str(page_number))  # ページ番号を追加
    can.save()

    packet.seek(0)
    return PyPDF2.PdfReader(packet).pages[0]

if __name__ == "__main__":
    output_pdf = "merged_output.pdf"
    input_pdfs = ["input1.pdf", "input2.pdf"] 
    # 結合したいPDFファイル名をリストに追加
