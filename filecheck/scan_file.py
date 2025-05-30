# scan_file.py

from pypdf import PdfReader
from spire.doc import *
from spire.doc.common import *
import re, argparse, os, pandas
from contextlib import redirect_stdout

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", type=str, help="Te scannen bestand (.pdf, .docx, .xlsx)", required=True)
parser.add_argument("-n", "--name", nargs='+', help="Naam of namen om te zoeken", default=[" "])
parser.add_argument("-o", "--outfile", action='store_true', help="Output ook naar out.txt bestand")
args = parser.parse_args()

term_size = os.get_terminal_size()

class PDFParcer:
    def __init__(self, file_name: str):
        self.pdf_object = PdfReader(file_name)
        self.pages_text = []
        self.page_parcer()

    def page_parcer(self):
        self.pages_text = [page.extract_text() for page in self.pdf_object.pages]

class DocxParcer:
    def __init__(self, file_name: str):
        self.document = Document()
        self.document.LoadFromFile(file_name)
        self.document_text = self.document.GetText()

class ExcelParcer:
    def __init__(self, file_name: str):
        self.exceldataframe = pandas.read_excel(file_name)
        self.exceldata = self.exceldataframe.to_string()

class TextAnalyzer(PDFParcer, DocxParcer, ExcelParcer):
    def __init__(self, filename: str, outfile: bool = False, names: list = []):
        _, extension = os.path.splitext(filename)
        match extension:
            case '.pdf':
                PDFParcer.__init__(self, file_name=filename)
                self.Email_match(list_text=self.pages_text)
                self.Phone_number_match(list_text=self.pages_text)
                self.Name_match(list_text=self.pages_text, names=names)
            case '.docx':
                DocxParcer.__init__(self, file_name=filename)
                self.Email_match(str_text=self.document_text)
                self.Phone_number_match(str_text=self.document_text)
                self.Name_match(str_text=self.document_text, names=names)
            case '.xlsx':
                ExcelParcer.__init__(self, file_name=filename)
                self.Email_match(str_text=self.exceldata)
                self.Phone_number_match(str_text=self.exceldata)
                self.Name_match(str_text=self.exceldata, names=names)
            case _:
                print("Gebruik een geldig bestandstype: .docx, .pdf, .xlsx")
                exit()
        if outfile:
            self.Out_file()
    
    def __repr__(self):
        newline = "\n"
        return f"""
{u'\u2015' * term_size.columns}
Emails gevonden:
{newline.join(self.emails)}

Telefoonnummers gevonden:
{newline.join(self.phonenumbers)}

Namen gevonden:
{newline.join(self.found_names)}
{u'\u2015' * term_size.columns}
"""

    def Email_match(self, str_text: str = None, list_text: list = None):
        found = []
        if str_text:
            found += re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', str_text)
        if list_text:
            for text in list_text:
                found += re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        self.emails = list(set(found))

    def Phone_number_match(self, str_text: str = None, list_text: list = None):
        found = []
        if str_text:
            found += re.findall(r'[\+\(]?[0-9][0-9 .\-\(\)]{8,}[0-9]', str_text)
        if list_text:
            for number in list_text:
                found += re.findall(r'[\+\(]?[0-9][0-9 .\-\(\)]{8,}[0-9]', number)
        self.phonenumbers = list(set(found))

    def Name_match(self, names: list, str_text: str = None, list_text: list = None):
        found_names = []
        if names == [" "]:
            self.found_names = ["Geen naam opgegeven met -n"]
            return
        try:
            if str_text:
                for name in names:
                    found_names += re.findall(name, str_text, re.IGNORECASE)
            if list_text:
                for text in list_text:
                    for name in names:
                        found_names += re.findall(name, text, re.IGNORECASE)
        except:
            found_names.append("Fout bij zoeken naar namen")
        self.found_names = list(set(found_names))

    def Out_file(self, filename: str = "out.txt"):
        newline = "\n"
        with open(filename, 'w', encoding="utf-8") as f:
            with redirect_stdout(f):
                print(self)

if __name__ == "__main__":
    analyzer = TextAnalyzer(filename=args.file, outfile=args.outfile, names=args.name)
    print(analyzer)

