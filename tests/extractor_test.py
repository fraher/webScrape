import os
import io
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from app.models.datatypes import OutputFormat
from app.services.pdfextractor import PDFExtractor
import pyarrow.parquet as pq

@pytest.fixture
def pdf_content():
    with open("tests/mock_data/pdfs/test_tables.pdf", "rb") as f:
        return f.read()

@pytest.fixture
def mock_urls():
    # This is where you'd specify any URLs you are pretending to download PDFs from for testing.
    return ["http://example.com/test_tables.pdf"]

@pytest.fixture
def expected_extraction_csv():
    # Load the expected DataFrame content from the CSV file
    csv_path = os.path.join(os.path.dirname(__file__), 'truth', 'test_tables.csv')
    return pd.read_csv(csv_path)

@pytest.fixture
def expected_extraction_parquet():
    # Load the expected DataFrame content from the CSV file
    parquet_path = os.path.join(os.path.dirname(__file__), 'truth', 'test_tables.parquet')
    return pd.read_parquet(parquet_path, engine="pyarrow")

def test_pdf_csv_extractor(pdf_content, mock_urls, expected_extraction_csv):
    """Test the PDFExtractor to verify extraction matches truth."""

    # Patch the requests.get call to return the mocked PDF content
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_get.return_value = mock_response
        
        # Initiating the PDFExtractor for the test
        extractor = PDFExtractor()
                
        buffer, _, _ = extractor.extract(mock_urls, OutputFormat.CSV.value)
        
        # Reading the CSV content from the buffer
        if buffer:
            extracted_df = pd.read_csv(io.StringIO(buffer.getvalue().decode("utf-8"))) 
            
            # Here we verify that the extracted DataFrame matches the expected DataFrame
            pd.testing.assert_frame_equal(extracted_df, expected_extraction_csv)
        else:
            pytest.fail("No data was extracted from the PDF")

def test_pdf_csv_extractor_incorrect_truth(pdf_content, mock_urls, expected_extraction_csv):
    """Negative test to verify the PDFExtractor assert fails with incorrect truth."""
    
    # Patch the requests.get call to return the mocked PDF content
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_get.return_value = mock_response
        
        # Initiating the PDFExtractor for the test
        extractor = PDFExtractor()
                
        buffer, _, _ = extractor.extract(urls=mock_urls, output_format=OutputFormat.CSV.value)
        
        # Reading the CSV content from the buffer
        if buffer:
            extracted_df = pd.read_csv(io.StringIO(buffer.getvalue().decode("utf-8"))) 

            # Modify the extracted DataFrame to simulate incorrect data
            extracted_df.columns = [col + "_modified" for col in extracted_df.columns]
            if not extracted_df.empty:
                extracted_df.iloc[0, 0] = "incorrect_data"
            
            # Here we verify that the extracted DataFrame does not match the expected DataFrame
            with pytest.raises(AssertionError):
                pd.testing.assert_frame_equal(extracted_df, expected_extraction_csv)
        else:
            pytest.fail("No data was extracted from the PDF")

def test_pdf_parquet_extractor(pdf_content, mock_urls, expected_extraction_parquet):
    """Test the PDFExtractor to verify extraction matches truth."""

    # Patch the requests.get call to return the mocked PDF content
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_get.return_value = mock_response
        
        # Initiating the PDFExtractor for the test
        extractor = PDFExtractor()
        
        buffer, _, _ = extractor.extract(urls=mock_urls, output_format=OutputFormat.PARQUET.value)
        
        # Reading the parquet content from the buffer
        if buffer:
            extracted_df = pd.read_parquet(io.BytesIO(buffer.getvalue()))
            
            # Here we verify that the extracted DataFrame matches the expected DataFrame
            pd.testing.assert_frame_equal(extracted_df, expected_extraction_parquet)
        else:
            pytest.fail("No data was extracted from the PDF")

def test_pdf_parquet_extractor_incorrect_truth(pdf_content, mock_urls, expected_extraction_parquet):
    """Negative test to verify the PDFExtractor assert fails with incorrect truth."""
    
    # Patch the requests.get call to return the mocked PDF content
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_get.return_value = mock_response
        
        # Initiating the PDFExtractor for the test
        extractor = PDFExtractor()
                
        buffer, _, _ = extractor.extract(urls=mock_urls, output_format=OutputFormat.PARQUET.value)
        
        # Reading the parquet content from the buffer
        if buffer:
            extracted_df = pd.read_parquet(io.BytesIO(buffer.getvalue())) 

            # Modify the extracted DataFrame to simulate incorrect data
            extracted_df.columns = [col + "_modified" for col in extracted_df.columns]
            if not extracted_df.empty:
                extracted_df.iloc[0, 0] = "incorrect_data"
            
            # Here we verify that the extracted DataFrame does not match the expected DataFrame
            with pytest.raises(AssertionError):
                pd.testing.assert_frame_equal(extracted_df, expected_extraction_parquet)
        else:
            pytest.fail("No data was extracted from the PDF")

