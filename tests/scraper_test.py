import pytest
import requests
from unittest.mock import patch, MagicMock
from app.models.datatypes import FileType
from app.routes.files import DiscoverRequest
from app.services.webscraper import WebScraper

@pytest.fixture
def mock_pdf_file():
    """Fixture that provides HTML content with PDF links."""
    return """
    <html>
        <body>
            <a href="http://testserver/file1.pdf">PDF1</a>
            <a href="http://testserver/file2.pdf">PDF2</a>
        </body>
    </html>
    """

@pytest.fixture
def mock_no_pdf_file():
    """Fixture that provides HTML content with no PDF links."""
    return """
    <html>
        <body>
            <p>No links here</p>
        </body>
    </html>
    """

@pytest.fixture
def mock_scraper():
    """Fixture that creates a WebScraper instance with an HTTP URL."""
    request = DiscoverRequest(url="http://testserver/test_has_pdfs.html", type=FileType.PDF)
    return WebScraper(request)

def test_scrape_with_valid_html(mock_scraper, mock_pdf_file):
    """Mock HTTP request for a page that contains PDF links."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_pdf_file

    with patch("requests.get", return_value=mock_response):
        result = mock_scraper.scrape()
    
    expected = ["http://testserver/file1.pdf", "http://testserver/file2.pdf"]
    assert result == expected

def test_scrape_with_no_links(mock_scraper, mock_no_pdf_file):
    """Mock HTTP request for a page with no PDF links."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_no_pdf_file

    with patch("requests.get", return_value=mock_response):
        result = mock_scraper.scrape()

    assert result == []

def test_scrape_with_http_error(mock_scraper):
    """Mock an HTTP error (e.g., 404 Not Found)."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            mock_scraper.scrape()
