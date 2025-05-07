import PyPDF2
import docx

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return '\n'.join([para.text for para in doc.paragraphs])
