import datetime
import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class URLScraper:
    """
    A web scraper that fetches URLs and PDF links from a webpage.

    Attributes:
        url (str): The starting URL to scrape.
        soup (Optional[BeautifulSoup]): Parsed HTML of the webpage.
        urls (List[str]): Unique list of discovered URLs on the webpage.
        pdf_urls (List[str]): List of PDF URLs on the weThis is request sentbpage.
    """

    def __init__(self, url: str):
        """
        Initializes the URLScrapper class and fetches URLs from the given webpage.

        Args:
            url (str): The URL of the webpage to scrape.
        """
        self.url = url
        self.session = requests.Session()
        self.soup = self._fetch_soup()
        self.urls = self.fetch_unique_urls()

    def __del__(self):
        """ Destructor method to clean up resources. """
        if hasattr(self, 'session'):
            self.session.close()

    def _fetch_soup(self, url: Optional[str] = None, year: int = None, month: int = None) -> Optional[BeautifulSoup]:
        """
        Fetches and parses HTML content of a URL.

        Args:
            url (str): The URL to fetch.
            year (int): Year for which to fetch circulars
            month (int): Month for which to fetch circulars

        Returns:
            Optional[BeautifulSoup]: BeautifulSoup object of the url, or None if request fails.
        """
        url = url or self.url
        try:
            initial_response = self.session.get(url)
            initial_response.raise_for_status()
            initial_soup = BeautifulSoup(initial_response.content, 'html.parser')
            if year and month is not None:
                viewstate = initial_soup.find("input", {"name": "__VIEWSTATE"})["value"]
                viewstate_generator = initial_soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
                event_validation = initial_soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

                cookies = initial_response.cookies.get_dict()

                payload = {
                    "__EVENTARGUMENT": "",
                    "__EVENTTARGET": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstate_generator,
                    "__EVENTVALIDATION": event_validation,
                    "hdnYear": year,
                    "hdnMonth": month,
                    "UsrFontCntr$txtSearch": "",
                    "UsrFontCntr$btn": ""
                }

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": self.url,
                }

                post_response = self.session.post(url, headers=headers, cookies=cookies, data=payload)
                post_response.raise_for_status()
                return BeautifulSoup(post_response.content, 'html.parser')

            return initial_soup

        except requests.exceptions.SSLError:
            logging.warning(f"SSL verification failed for {url}. Retrying without verification...")
            try:
                self.session.verify = False
                response = self.session.get(url)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as err:
                logging.warning(f"Error fetching {url}: {err}")
        except requests.exceptions.RequestException as err:
            logging.warning(f"Error fetching {url}: {err}")
            return None

    def fetch_all_urls(self, url: Optional[str] = None) -> List[str]:
        """
        Extracts all URLs from the given webpage.

        Args:
            url (str): The URL of the webpage to extract URLs from.

        Returns:
            List[str]: Unique list of discovered URLs on the webpage.
        """
        url = url or self.url
        soup = self._fetch_soup(url) if url != self.url else self.soup
        return [
            urljoin(url, link['href'])
            for link in soup.find_all('a', href=True)
            if urljoin(url, link['href']).startswith("http")
        ]

    def fetch_unique_urls(self, url: Optional[str] = None) -> List[str]:
        """
        Fetches and removes duplicate URLs.

        Args:
            url (Optional[str]): The URL of the webpage to extract unique URLs from.
        Returns:
            List[str]: Unique list of discovered URLs on the webpage.
        """
        url = url or self.url
        return list(set(self.fetch_all_urls(url)))

    # noinspection PyIncorrectDocstring
    def filter_urls(self, pattern: str, urls: Optional[List[str]] = None) -> List[str]:
        """
        Filters URLs based on a regex pattern.

        Args:
            pattern (str): The regex pattern to filter URLs for.
            urls (Optional[List[str]]): The URLs to filter.
        Returns:
            List[str]: Unique list of discovered URLs on the webpage.
        """
        urls = urls or self.urls
        return [url for url in urls if re.search(pattern=pattern, string=url)]

    def recursive_url_parser(self, page_layer: str, url_layer: Optional[str] = None) -> List[str]:
        """
        Recursively finds PDFs from URLs matching a given pattern.

        Args:
            page_layer (str): Regex pattern to filter webpages.
            url_layer (Optional[str]): Regex pattern to filter URLs within webpages.

        Returns:
            List[str]: All discovered PDF URLs.
        """
        matches = self.filter_urls(pattern=page_layer, urls=self.fetch_unique_urls(url=self.url))
        return matches

    def get_circular_by_date(self, month: int = None, year: int = None):
        if month and year is None:
            month, year = datetime.date().month, datetime.date().year
        self.soup = self._fetch_soup(month=month, year=year)

        return self.recursive_url_parser(page_layer=r'^https:\/\/rbi\.org\.in\/Scripts\/BS_CircularIndexDisplay\.aspx\?Id=\d+$', url_layer=r'https://rbidocs\.rbi\.org\.in/rdocs/Notification/PDFs/[^\"\s]+\.PDF')