import os.path
import re
import requests
import logging
from bs4 import BeautifulSoup
from typing import List
from urlscraper import URLScraper
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Circular:
    def __init__(self, circular_url: str):
        """
        Initializes a Circular object to represent and process an RBI circular.

        Args:
            circular_url (str): The URL of the circular webpage.
        """
        self._id: str | None = None
        self.url: str = circular_url
        self.title: str | None = None
        self.tags: List[str] = []
        self.date: str | None = None
        self.bookmark: str | None = None
        self.path: str = "ui/public/pdfs"
        self.conversation_id: str | None = None
        self.references: str | None = None
        self.pdf_url: str | None = None

    def __repr__(self) -> str:
        """
        Returns a string representation of the Circular object.

        Returns:
            str: A formatted string with all the circular's attributes.
        """
        return (f"_id = {self._id}\n"
                f"title = {self.title}\n"
                f"tags = {self.tags}\n"
                f"date = {self.date}\n"
                f"bookmark = {self.bookmark}\n"
                f"path = {self.path}\n"
                f"conversation_id = {self.conversation_id}\n"
                f"references = {self.references}\n"
                f"pdf_url = {self.pdf_url}")

    def fetch_pdf_url(self) -> str:
        """
        Extracts the PDF URL from the circular webpage.

        Returns:
            str: The URL of the circular's PDF document.

        Raises:
            ValueError: If no matching PDF URL is found.
        """
        try:
            scraper = URLScraper(url=self.url)
            pdf_url = scraper.filter_urls(r"https://rbidocs\.rbi\.org\.in/rdocs/Notification/PDFs/[^\"\s]+\.PDF")
            if not pdf_url:
                raise ValueError("No PDF URL found on the webpage.")
            self.pdf_url = pdf_url[0]
            return self.pdf_url
        except Exception as e:
            logging.error(f"Error fetching PDF URL: {e}")
            raise

    def fetch_metadata(self) -> None:
        """
        Scrapes and updates the circular's metadata, including title, circular ID, and date.

        Raises:
            requests.HTTPError: If the request to the circular webpage fails.
        """
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title_tag = soup.select_one('tr td.tableheader b')
            if title_tag:
                self.title = title_tag.get_text(strip=True)

            circular_info_tag = soup.select_one('tr td p')
            if circular_info_tag:
                circular_text = circular_info_tag.get_text(separator='\n', strip=True)
                circular_number_match = re.search(
                    r'RBI/\d{2,4}-\d{2,4}/\d+|[A-Z]+\.No\.[A-Z]+(\.[A-Z]+)?\.\d+/\d{2}\.\d{2}\.\d+/\d{4}-\d{2}',
                    circular_text,
                    re.S
                )
                if circular_number_match:
                    self._id = circular_text.replace('\n', '-')

            date_tags = soup.find_all('p', align='right')
            date_pattern = re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}$')
            for tag in date_tags:
                if date_pattern.match(tag.get_text(strip=True)):
                    self.date = tag.get_text(strip=True)
                    break

            pdf_url = soup.find('a', href=re.compile(r'https://rbidocs\.rbi\.org\.in/rdocs/Notification/PDFs/[^"\s]+\.PDF'))
            if pdf_url:
                self.pdf_url = pdf_url['href']

        except requests.RequestException as e:
            logging.error(f"Error fetching metadata: {e}")
            raise

    def download_pdf(self, path: str = None) -> bool:
        """
        Downloads the circular's PDF to the specified path.

        Args:
            path (str, optional): Directory to save the downloaded PDF.
                Defaults to the class attribute `self.path`.

        Returns:
            bool: True if the PDF download is successful, False otherwise.

        Raises:
            requests.RequestException: If the request to download the PDF fails.
        """
        try:
            if self.pdf_url is None:
                logging.info("PDF URL not set. Trying to fetch PDF URL...")
                self.fetch_pdf_url()
                if self.pdf_url is None:
                    logging.error("Failed to fetch PDF URL.")
                    return False

            path = path or self.path
            if not path:
                logging.error("PDF path not set.")
                return False

            response = requests.get(self.pdf_url)
            response.raise_for_status()

            root = Path(__file__).parent.parent.parent
            self.path = root / path / os.path.basename(self.pdf_url)
            logging.info(self.path)

            with open(self.path, "wb") as pdf_file:
                logging.info("opened")
                pdf_file.write(response.content)
            logging.info(f"Downloaded successfully: {os.path.join(path, os.path.basename(self.pdf_url))}")
            return True

        except (requests.RequestException, IOError) as e:
            logging.error(f"Error downloading PDF: {e}")
            return False


if __name__ == "__main__":
    url = "https://rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx?Id=12611"
    c = Circular(url)

    try:
        c.fetch_metadata()
        if c.download_pdf():
            print(c)
    except Exception as e:
        logging.error(f"Process failed: {e}")
