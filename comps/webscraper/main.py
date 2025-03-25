from comps import CustomLogger
from urlscraper import URLScraper
from circular import Circular
from fastapi import Request
from fastapi.responses import JSONResponse
import os
import requests
from pathlib import Path
from comps import  MicroService, ServiceRoleType

logger = CustomLogger("web_scraper")
server_host_ip = os.getenv("SERVER_HOST_IP")
server_port = os.getenv("SERVER_PORT")
dataprep_host_ip = os.getenv("DATAPREP_HOST_IP")
dataprep_port = os.getenv("DATAPREP_PORT")
    
class WebScraperService:
    def __init__(self, host="0.0.0.0", port=8002):
        self.host = host
        self.port = port
        self.endpoint = "/v1/scrape"
        
    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
        )

        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.start()

    def post_circular_to_api(self, circular: Circular):
        data = {
            '_id': circular._id,
            'title': circular.title,
            'tags': circular.tags,
            'date': circular.date,
            'bookmark': circular.bookmark,
            'path': str(circular.path),
            'conversation_id': circular.conversation_id,
            'references': circular.references,
            'pdf_url': circular.pdf_url
        }
        url = f"http://{server_host_ip}:{server_port}/api/circulars"
        response = requests.post(url, json=data)
        if response.status_code == 200:
            logger.info(f"Success: {response.json()}")
        else:
            logger.info(f"Failed: {response.status_code} {response.text}")
        
    def send_request_to_dataprep(self, pdf_url: str):
        url = f"http://{dataprep_host_ip}:{dataprep_port}/v1/dataprep"
        files = {'files': open(pdf_url, 'rb')}
        data = {'parser_type': 'lightweight'}
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            logger.info(f"Success: {response.json()}")
        else:
            logger.info(f"Failed: {response.status_code} {response.text}")

    async def handle_request(self, request: Request):
        try:
            data = await request.json()
            scraper = URLScraper("https://rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx")
            pdf_urls = scraper.get_circular_by_date(data['month'], data['year'])
            logger.info(f"Found {len(pdf_urls)} PDFs: {pdf_urls}")

            for pdf_url in pdf_urls:
                c = Circular(pdf_url)
                c.fetch_metadata()
                if c.download_pdf():
                    print(c)
                    self.post_circular_to_api(c)
                    root = Path(__file__).parent.parent.parent
                    s = "ui/public" + str(c.path)
                    path = root / s
                    self.send_request_to_dataprep(path)

            return JSONResponse(
                content={"status": "success"},
                status_code=200
            )
        except Exception as e:
            logger.info(e)

if __name__ == "__main__":
    web_scraper_service = WebScraperService(port=8002)
    web_scraper_service.start()