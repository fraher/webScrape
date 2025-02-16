from app.services.scraper import Scraper
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

class WebScraper(Scraper):
    
    def scrape(self):        
        # Send an HTTP request to fetch the page content
        response = requests.get(self.url)
        response.raise_for_status()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if not hasattr(self, 'css_selector') or self.css_selector is None:
            parsed_data = [
                urljoin(self.url, a['href']) for a in soup.find_all('a', href=True)
                if a['href'].endswith(self.file_type.value)
                ]
        else:
            parsed_data = [
                urljoin(self.url, a['href']) for el in soup.select(self.css_selector)
                for a in el.find_all('a', href=True) 
                if a.get('href') and a['href'].endswith(self.file_type.value)
                ]
        return parsed_data