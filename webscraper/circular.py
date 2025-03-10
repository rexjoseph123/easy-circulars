import datetime
import os.path
import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Optional
from urlscraper import URLScraper
from pdfplumber import pdf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Circular:
    def __init__(self, circular_url):
        self._id = None
        self.url = circular_url
        self.title = None
        self.tags = []
        self.date = None
        self.bookmark = None
        self.path = "ui/public/pdfs"
        self.conversation_id = None
        self.references = None
        self.pdf_url = None

    def __repr__(self):
            return f"_id = {self._id}\ntitle = {self.title}\ntags = {self.tags}\ndate = {self.date}\nbookmark = {self.bookmark}\npath = {self.path}\nconversation_id = {self.conversation_id}\nreferences = {self.references}\npdf_url = {self.pdf_url}"

    def fetch_pdf_url(self):
        scraper = URLScraper(url=self.url)
        pdf_url = scraper.filter_urls(r"https://rbidocs\.rbi\.org\.in/rdocs/Notification/PDFs/[^\"\s]+\.PDF")
        self.pdf_url = pdf_url[0]

    def fetch_metadata(self):
        response = requests.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title using a CSS selector for <tr> > <td.tableheader> > <b>
        title_tag = soup.select_one('tr td.tableheader b')

        if title_tag:
            self.title = title_tag.get_text(strip=True)

        circular_info_tag = soup.select_one('tr td p')
        if circular_info_tag:
            # Use '\n' as separator for <br> converted to newline
            circular_text = circular_info_tag.get_text(separator='\n', strip=True)
            # Regex: first line matches RBI/... and second line matches CO....
            circular_number_match = re.search(
                r'(RBI/\d{4}-\d{2,4}/\d+)\s*[\r\n]+\s*(CO\.[^\r\n]+)',
                circular_text,
                re.S
            )
            if circular_number_match:
                circular_number_rbi = circular_number_match.group(1)
                circular_number_co = circular_number_match.group(2)
                self._id = circular_number_rbi + '-' + circular_number_co

        date_tags = soup.find_all('p', align='right')
        date_pattern = re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}$')
        for tag in date_tags:
            if date_pattern.match(tag.get_text(strip=True)):
                self.date = tag.get_text(strip=True)
                break

        pdf_url = soup.find('a', href=re.compile(r'https://rbidocs\.rbi\.org\.in/rdocs/Notification/PDFs/[^"\s]+\.PDF'))
        if pdf_url is not None:
            self.pdf_url = pdf_url['href']


    def download_pdf(self, path=None):
        if self.pdf_url is None:
            print("PDF url not set.\nTrying to fetch PDF url")
            self.fetch_pdf_url()
            if self.pdf_url is None:
                return "Failed to fetch PDF url"

        path = path or self.path
        if path is None:
            return "PDF path not set."
        response = requests.get(self.pdf_url)
        if response.status_code == 200:
            with open(os.path.join(self.path, os.path.basename(self.pdf_url)), "wb") as pdf_file:
                pdf_file.write(response.content)
            return "Downloaded successfully."
        return "Failed to download."

if __name__ == "__main__":
    url = "https://rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx?Id=12789"
    c = Circular(url)
    c.fetch_metadata()
    x = c.download_pdf()
    print(x)
    print(c)
