import os.path
import re
import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Optional
from urlscraper import URLScraper
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Circular:
    def __init__(self, circular_url: str):
        """
        Initializes a Circular object to represent and process an RBI circular.

        Args:
            circular_url (str): The URL of the circular webpage.
        """
        self._id: str | None = None
        self.core_id: str | None = None
        self.url: str = circular_url
        self.title: str | None = None
        self.tags: List[str] = []
        self.date: datetime | None = None
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
                f"core_id = {self.core_id}\n"
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

    def _parse_core_id(self, full_id: str) -> Optional[str]:
        """
        Parses the core identifier from the full circular ID string.
        Attempts to extract patterns like 'XX.XX.XXX'.
        """
        core_id_match = re.search(r'(\d{2}\.\d{2}\.\d+)', full_id)
        if core_id_match:
            return core_id_match.group(1)
        logging.warning(f"Could not extract core ID from: {full_id}")
        return None

    def fetch_metadata(self) -> None:
        """
        Scrapes and updates the circular's metadata, including title, circular ID, core ID, and date.

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
                    r'(RBI/\d{4}-\d{4}/\d+|RBI/\d{4}-\d{2}/\d+)|'
                    r'([A-Z]+\.No\.[A-Z]+(?:\.[A-Z]+)?\.\d+/\d{2}\.\d{2}\.\d+/\d{4}-\d{2})',
                    circular_text,
                    re.IGNORECASE | re.S
                )
                if circular_number_match:
                    full_id = circular_number_match.group(2) or circular_number_match.group(1)
                    if full_id:
                        self._id = re.sub(r'\s+', ' ', full_id).strip()
                        self.core_id = self._parse_core_id(self._id)
                    else:
                        logging.warning(f"Circular ID regex matched but no group captured text: {circular_text}")
                else:
                    logging.warning(f"Could not find circular ID pattern in: {circular_text}")

            date_tags = soup.find_all('p', align='right')
            date_pattern = re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}$')
            for tag in date_tags:
                date_string = tag.get_text(strip=True)
                if date_pattern.match(date_string):
                    try:
                        self.date = datetime.strptime(date_string, "%B %d, %Y")
                        logging.info(f"Found date: {self.date}")
                        break
                    except ValueError as e:
                        logging.warning(f"Date parsing error for '{date_string}': {e}")
            if not self.date:
                logging.warning(f"Could not find date on page: {self.url}")

            if not self.pdf_url:
                pdf_link_tag = soup.find('a', href=re.compile(r'https://rbidocs\.rbi\.org\.in/rdocs/Notification/PDFs/[^"\s]+\.PDF', re.IGNORECASE))
                if pdf_link_tag and pdf_link_tag.get('href'):
                    self.pdf_url = pdf_link_tag['href']
                else:
                    logging.warning(f"Could not find PDF link tag on page: {self.url}")

        except requests.RequestException as e:
            logging.error(f"Error fetching metadata for {self.url}: {e}")
            raise
        except Exception as e:
            logging.error(f"Error parsing metadata for {self.url}: {e}")
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
                    logging.error("Failed to fetch PDF URL after explicit attempt.")
                    return False

            path_prefix = path or self.path
            if not path_prefix:
                logging.error("PDF download path prefix not set.")
                return False

            if not isinstance(self.pdf_url, str) or not self.pdf_url.startswith('http'):
                logging.error(f"Invalid PDF URL for download: {self.pdf_url}")
                return False

            response = requests.get(self.pdf_url, stream=True)
            response.raise_for_status()

            root = Path(__file__).parent.parent.parent
            download_dir = root / path_prefix
            download_dir.mkdir(parents=True, exist_ok=True)

            filename = os.path.basename(self.pdf_url)
            if not filename.lower().endswith('.pdf'):
                filename += ".pdf"
                logging.warning(f"Appended .pdf extension to filename derived from {self.pdf_url}")

            self.path = download_dir / filename

            logging.info(f"Attempting to download PDF to: {self.path}")

            with open(self.path, "wb") as pdf_file:
                for chunk in response.iter_content(chunk_size=8192):
                    pdf_file.write(chunk)

            logging.info(f"Downloaded successfully: {self.path}")
            try:
                self.path = Path("/pdfs") / filename
            except TypeError as e:
                logging.error(f"Error creating relative path: {e}. Using full path.")
            return True

        except requests.RequestException as e:
            logging.error(f"HTTP Error downloading PDF from {self.pdf_url}: {e}")
            return False
        except IOError as e:
            logging.error(f"File system error saving PDF to {self.path}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error downloading PDF {self.pdf_url}: {e}")
            return False