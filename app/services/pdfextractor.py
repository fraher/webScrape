import io
import os
import uuid
import zipfile
import pandas as pd
import pdfplumber
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from .extractor import Extractor

class PDFExtractor(Extractor):
    def clean_header(self, header):
        """Normalize headers by removing special characters, extra spaces, and handling duplicates."""
        if isinstance(header, str):
            return re.sub(r'\s+', ' ', header).strip()  # Remove newlines, multiple spaces
        return "Unknown Column" if header is None else str(header)  # Handle NoneType headers

    def is_valid_header(self, row):
        """Check if a row is a valid header (contains mostly strings, not numbers)."""
        if not isinstance(row, list):
            return False
        return sum(isinstance(item, str) for item in row) > (len(row) // 2)  # Majority should be strings

    def reshape_table(self, table):
        """Ensure extracted tables maintain correct row structure."""
        if not table or len(table) < 2:
            return None  # Skip malformed tables
        return table

    def fetch_and_extract(self, url, output_dir, single_file):
        """Download and extract tables from a single PDF file and save as a single CSV."""
        try:
            print(f"Processing: {url}")

            # Fetch PDF
            pdf_response = requests.get(url, timeout=10, stream=True)
            pdf_response.raise_for_status()

            # Convert bytes to file-like object
            pdf_file = io.BytesIO(pdf_response.content)

            extracted_tables = []
            pdf_headers = None
            pdf_filename = os.path.basename(url).replace('.pdf', '.csv')
            pdf_filepath = os.path.join(output_dir, pdf_filename)
            
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        table = self.reshape_table(table)  # Reshape table to correct row structure
                        if not table:
                            continue  # Skip empty or malformed tables
                        
                        df = pd.DataFrame(table)
                        df = df.dropna(how='all')  # Drop fully empty rows
                        
                        if df.empty:
                            continue  # Ensure we still have data
                        
                        # Determine if first row is a valid header
                        if self.is_valid_header(df.iloc[0].tolist()):
                            pdf_headers = [self.clean_header(col) for col in df.iloc[0]]  # Normalize headers
                            df = df[1:]  # Remove header row from data
                        
                        # Ensure table has headers from the PDF
                        if pdf_headers:
                            df.columns = pdf_headers
                        else:
                            df.columns = [f"Column_{i}" for i in range(len(df.columns))]  # Auto-generate headers
                        
                        df = df.reset_index(drop=True)
                        
                        if df.empty:
                            continue  # Ensure table is still valid
                        
                        extracted_tables.append(df)

            if extracted_tables:
                final_pdf_df = pd.concat(extracted_tables, ignore_index=True)
                if not single_file:
                    final_pdf_df.to_csv(pdf_filepath, index=False)

            print(f"Completed processing: {url}")
            return extracted_tables if extracted_tables else None
        except requests.RequestException as req_err:
            print(f"Request error for {url}: {req_err}")
        except Exception as e:
            print(f"Unexpected error processing {url}: {e} (File: {url})")
        return None

    def extract(self, urls: list, single_file=True):
        """Extract tables from multiple PDF files in parallel. If single_file=True, process in memory; otherwise, store and zip CSVs."""
        execution_id = uuid.uuid4().hex
        output_dir = f"extraction_{execution_id}"
        os.makedirs(output_dir, exist_ok=True)

        all_dfs = []

        # Use ThreadPoolExecutor for efficient I/O-bound parallelism
        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as executor:
            future_to_url = {executor.submit(self.fetch_and_extract, url, output_dir, single_file): url for url in urls}
            for future in as_completed(future_to_url):
                try:
                    result = future.result()
                    if result and single_file:
                        all_dfs.extend(result)  # Keep all extracted data in memory
                except Exception as e:
                    print(f"Error processing PDF: {future_to_url[future]}, Error: {e} (File: {future_to_url[future]})")

        if single_file:
            if all_dfs:
                final_df = pd.concat(all_dfs, ignore_index=True)
                buffer = io.StringIO()
                final_df.to_csv(buffer, index=False)
                buffer.seek(0)

                headers = {
                    'Content-Disposition': 'attachment; filename="final_extracted_data.csv"'
                }
                return buffer, 'text/csv', headers
            else:
                print("No valid tables were extracted.")
                return None
        else:
            # Zip all extracted CSVs and return
            zip_filename = f"{output_dir}.zip"
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for csv_file in os.listdir(output_dir):
                    csv_path = os.path.join(output_dir, csv_file)
                    if csv_file.endswith(".csv"):
                        zipf.write(csv_path, os.path.basename(csv_path))
            
            buffer = io.BytesIO()
            with open(zip_filename, "rb") as f:
                buffer.write(f.read())
            buffer.seek(0)

            # Cleanup temporary folder
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)
            os.remove(zip_filename)
            
            headers = {
                'Content-Disposition': f'attachment; filename="extracted_pdfs.zip"'
            }
            return buffer, 'application/zip', headers
