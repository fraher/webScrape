import io
import pandas as pd
import pdfplumber
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
import re
from .extractor import Extractor

class PDFExtractor(Extractor):
    def clean_header(self, header):
        """Normalize headers by removing special characters and extra spaces."""
        if isinstance(header, str):
            return re.sub(r'\s+', ' ', header).strip()  # Remove newlines, multiple spaces
        return header

    def fetch_and_extract(self, url):
        """Download and extract tables from a single PDF file"""
        try:
            print(f"Processing: {url}")

            # Fetch PDF
            pdf_response = requests.get(url, timeout=10)
            pdf_response.raise_for_status()

            # Convert bytes to file-like object
            pdf_file = io.BytesIO(pdf_response.content)

            extracted_tables = []
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        if not table:
                            continue  # Skip empty tables
                        df = pd.DataFrame(table)
                        
                        if df.empty:
                            continue  # Skip empty dataframes
                        
                        df = df.dropna(how='all')  # Drop empty rows
                        
                        if df.empty:
                            continue  # Ensure we still have data
                        
                        df.columns = [self.clean_header(col) for col in df.iloc[0]]  # Normalize headers
                        df = df[1:]  # Remove header row without resetting index
                        
                        if df.empty:
                            continue  # Ensure table is still valid
                        
                        extracted_tables.append(df)

            return extracted_tables if extracted_tables else None
        except requests.RequestException as req_err:
            print(f"Request error for {url}: {req_err}")
        except pdfplumber.PDFSyntaxError as pdf_err:
            print(f"PDF parsing error for {url}: {pdf_err}")
        except Exception as e:
            print(f"Unexpected error processing {url}: {e}")
        return None

    def extract(self, urls: list):
        """Extract tables from multiple PDF files in parallel"""
        all_tables = []
        unique_headers = set()
        structured_data = []

        # Use ProcessPoolExecutor to process PDFs in parallel
        with ProcessPoolExecutor() as executor:
            future_to_url = {executor.submit(self.fetch_and_extract, url): url for url in urls}

            for future in as_completed(future_to_url):
                try:
                    result = future.result()
                    if result:
                        for df in result:
                            df.columns = [self.clean_header(col) for col in df.columns]  # Normalize headers
                            unique_headers.update(df.columns)
                            structured_data.append(df)
                except Exception as e:
                    print(f"Error processing PDF: {future_to_url[future]}, Error: {e}")

        # Build final DataFrame ensuring consistent headers
        if structured_data:
            final_df = pd.DataFrame(columns=sorted(unique_headers))
            for df in structured_data:
                final_df = pd.concat([final_df, df.reindex(columns=final_df.columns)], ignore_index=True)

            buffer = io.StringIO()
            final_df.to_csv(buffer, index=False)  # Ensure final output does not include index
            buffer.seek(0)

            headers = {
                'Content-Disposition': 'attachment; filename="extracted_tables.csv"'
            }

            return buffer, 'text/csv', headers
        else:
            print("No valid tables were extracted.")
            return None
