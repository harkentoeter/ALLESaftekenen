import os
import re
import argparse
import pandas
from contextlib import redirect_stdout
from pypdf import PdfReader
from spire.doc import *
from spire.doc.common import *

argumenten = argparse.ArgumentParser()
argumenten.add_argument("-f", "--bestand", type=str, help="Het bestand dat je wil scannen (.pdf, .docx, .xlsx)", required=True)
argumenten.add_argument("-n", "--namen", nargs='+', help="Naam of namen om te zoeken", default=[" "])
argumenten.add_argument("-o", "--uitvoerbestand", action='store_true', help="Resultaat ook opslaan in out.txt")
args = argumenten.parse_args()

term_grootte = os.get_terminal_size()

class PDFLezer:
    def __init__(self, bestandsnaam: str):
        self.pdf = PdfReader(bestandsnaam)
        self.paginas_tekst = []
        self.tekst_uit_paginas()

    def tekst_uit_paginas(self):
        self.paginas_tekst = [pagina.extract_text() for pagina in self.pdf.pages]

class WordLezer:
    def __init__(self, bestandsnaam: str):
        self.document = Document()
        self.document.LoadFromFile(bestandsnaam)
        self.tekst = self.document.GetText()

class ExcelLezer:
    def __init__(self, bestandsnaam: str):
        self.dataframe = pandas.read_excel(bestandsnaam)
        self.tekst = self.dataframe.to_string()

class TekstScanner(PDFLezer, WordLezer, ExcelLezer):
    def __init__(self, bestandsnaam: str, uitvoer_naar_bestand: bool = False, zoek_namen: list = []):
        _, extensie = os.path.splitext(bestandsnaam)
        if extensie == '.pdf':
            PDFLezer.__init__(self, bestandsnaam)
            self.vind_emails(teksten=self.paginas_tekst)
            self.vind_nummers(teksten=self.paginas_tekst)
            self.vind_namen(teksten=self.paginas_tekst, namen=zoek_namen)
        elif extensie == '.docx':
            WordLezer.__init__(self, bestandsnaam)
            self.vind_emails(tekst=self.tekst)
            self.vind_nummers(tekst=self.tekst)
            self.vind_namen(tekst=self.tekst, namen=zoek_namen)
        elif extensie == '.xlsx':
            ExcelLezer.__init__(self, bestandsnaam)
            self.vind_emails(tekst=self.tekst)
            self.vind_nummers(tekst=self.tekst)
            self.vind_namen(tekst=self.tekst, namen=zoek_namen)
        else:
            print("Gebruik een geldig bestandstype: .docx, .pdf, .xlsx")
            exit()

        if uitvoer_naar_bestand:
            self.schrijf_uitvoer()

    def __repr__(self):
        return f"""
{'―' * term_grootte.columns}
Gevonden e-mailadressen:
{'\n'.join(self.emails)}

Gevonden telefoonnummers:
{'\n'.join(self.nummers)}

Gevonden namen:
{'\n'.join(self.gevonden_namen)}
{'―' * term_grootte.columns}
"""

    def vind_emails(self, tekst: str = None, teksten: list = None):
        gevonden = []
        if tekst:
            gevonden += re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', tekst)
        if teksten:
            for stuk in teksten:
                gevonden += re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', stuk)
        self.emails = list(set(gevonden))

    def vind_nummers(self, tekst: str = None, teksten: list = None):
        gevonden = []
        if tekst:
            gevonden += re.findall(r'[\+\(]?[0-9][0-9 .\-\(\)]{8,}[0-9]', tekst)
        if teksten:
            for stuk in teksten:
                gevonden += re.findall(r'[\+\(]?[0-9][0-9 .\-\(\)]{8,}[0-9]', stuk)
        self.nummers = list(set(gevonden))

    def vind_namen(self, namen: list, tekst: str = None, teksten: list = None):
        gevonden = []
        if namen == [" "]:
            self.gevonden_namen = ["Geen naam opgegeven met -n"]
            return
        try:
            if tekst:
                for naam in namen:
                    gevonden += re.findall(naam, tekst, re.IGNORECASE)
            if teksten:
                for stuk in teksten:
                    for naam in namen:
                        gevonden += re.findall(naam, stuk, re.IGNORECASE)
        except:
            gevonden.append("Fout bij het zoeken naar namen")
        self.gevonden_namen = list(set(gevonden))

    def schrijf_uitvoer(self, bestandsnaam: str = "out.txt"):
        with open(bestandsnaam, 'w', encoding="utf-8") as f:
            with redirect_stdout(f):
                print(self)

if __name__ == "__main__":
    scanner = TekstScanner(bestandsnaam=args.bestand, uitvoer_naar_bestand=args.uitvoerbestand, zoek_namen=args.namen)
    print(scanner)

