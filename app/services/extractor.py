from abc import ABC, abstractmethod

class Extractor(ABC):    
    @abstractmethod
    def extract(self, urls: list):
        """Extract data from one or more multiple URLs and combine the results"""
        pass