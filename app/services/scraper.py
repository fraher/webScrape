from abc import ABC, abstractmethod

class Scraper(ABC):
    def __init__(self, request):
        self.url = request.url
        self.file_type = request.type
        self.css_selector = request.css_selector if hasattr(request, 'css_selector') else None

    @abstractmethod
    def scrape(self):
        """Extract data from a given URL"""
        pass
