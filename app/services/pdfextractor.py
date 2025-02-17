import io
import os
import uuid
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

import pdfplumber
import requests
import pandas as pd
import pyarrow.parquet as pq

# Adjust imports below to match your project structure
from .extractor import Extractor
from app.models import OutputFormat

class PDFExtractor(Extractor):
    def __init__(self, standard_headers=None):
        """
        standard_headers: list of column names that this document should have
                          if no valid header row is detected (fallback).
        """
        self.standard_headers = standard_headers

    def clean_header(self, header: str) -> str:
        """
        Removes newline/carriage returns and extra spaces.
        """
        if not isinstance(header, str):
            return "Unknown Column" if header is None else str(header)
        cleaned = header.replace('\n', ' ').replace('\r', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def is_valid_header(self, row, threshold=0.5) -> bool:
        """
        Returns True if 'row' is likely a real header:
          1) No empty cells.
          2) No purely numeric cells.
          3) At least 'threshold' fraction of cells are non-numeric text.
        """
        if not row:
            return False

        # Check for empty or purely numeric cells => invalid
        for cell in row:
            cell_str = str(cell).strip()
            if not cell_str or cell_str.isdigit():
                return False

        # Ensure at least 'threshold' fraction of cells are textual
        text_count = 0
        for item in row:
            s = str(item).strip()
            if s and not s.isdigit():
                text_count += 1

        ratio = text_count / len(row)
        return ratio >= threshold

    def reshape_table(self, table):
        """Skip malformed tables with too few rows."""
        if not table or len(table) < 2:
            return None
        return table

    def ensure_unique_columns(self, df: pd.DataFrame):
        """Make repeated column names distinct (Column, Column_1, etc.)."""
        seen = {}
        new_cols = []
        for col in df.columns:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_cols.append(col)
        df.columns = new_cols

    def fetch_and_extract(self, url):
        """
        Processes a single PDF, returns (list_of_dfs, chosen_header).

        Steps:
          - Gather raw tables from pdfplumber.
          - Determine the most frequent first row that passes is_valid_header.
          - If none is valid, fallback to standard_headers or [Column_0, ...].
          - Apply that chosen/fallback header, removing rows that match that header verbatim.
        """
        try:
            print(f"\n--- Processing: {url} ---")
            pdf_response = requests.get(url, timeout=10, stream=True)
            pdf_response.raise_for_status()
            pdf_file = io.BytesIO(pdf_response.content)

            raw_tables = []
            row_counts = {}

            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for tbl_idx, tbl in enumerate(tables):
                        reshaped = self.reshape_table(tbl)
                        if not reshaped:
                            continue

                        df = pd.DataFrame(reshaped).dropna(how='all')
                        if df.empty:
                            continue

                        # Clean the first row for consistent matching
                        cleaned_first_row = [
                            self.clean_header(str(x)) for x in df.iloc[0]
                        ]
                        first_row_tuple = tuple(cleaned_first_row)

                        # Track frequency
                        row_counts[first_row_tuple] = row_counts.get(first_row_tuple, 0) + 1

                        raw_tables.append(df)

            if not raw_tables:
                print(f"No valid tables found in {url}.")
                return None, None

            # Sort candidate rows by frequency desc
            sorted_candidates = sorted(
                row_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )

            chosen_header = None
            for row_tuple, freq in sorted_candidates:
                if self.is_valid_header(list(row_tuple)):
                    chosen_header = [self.clean_header(x) for x in row_tuple]
                    print(f"Chosen header (frequency={freq}) for {url}: {chosen_header}")
                    break

            # Fallback if no valid repeated header
            if not chosen_header:
                chosen_header = (
                    self.standard_headers
                    or [f"Column_{i}" for i in range(len(raw_tables[0].columns))]
                )
                print(f"No strong repeated header found; using fallback: {chosen_header}")

            chosen_header_tuple = tuple(chosen_header)
            final_dfs = []
            num_pdf_cols = len(chosen_header)

            for df in raw_tables:
                # Pad or trim columns
                if df.shape[1] < num_pdf_cols:
                    for _ in range(num_pdf_cols - df.shape[1]):
                        df[f"Extra_Col_{df.shape[1]}"] = None
                elif df.shape[1] > num_pdf_cols:
                    df = df.iloc[:, :num_pdf_cols]

                # Assign the chosen columns
                df.columns = chosen_header
                self.ensure_unique_columns(df)

                # Remove rows that exactly match chosen_header
                row_tuples = df.astype(str).apply(
                    lambda r: tuple(self.clean_header(x) for x in r),
                    axis=1
                )
                df = df[row_tuples != chosen_header_tuple].reset_index(drop=True)

                if not df.empty:
                    final_dfs.append(df)

            if final_dfs:
                print(f"Finished extracting {len(final_dfs)} table(s) from {url}.")
                return final_dfs, chosen_header
            else:
                print(f"All tables for {url} ended up empty after removing headers.")
                return None, chosen_header

        except requests.RequestException as req_err:
            print(f"Request error for {url}: {req_err}")
        except Exception as e:
            print(f"Unexpected error processing {url}: {e} (File: {url})")
        return None, None

    def extract(self, urls: list, output_format: OutputFormat = OutputFormat.CSV):
        """
        Orchestrate parallel PDF processing for the list of URLs,
        then unify columns using the globally most-used header.
        Finally, remove blank rows and stray repeated header rows.
        """
        # Instead of creating a local directory, we store in /tmp/web_scraper
        base_tmp_dir = "/tmp/web_scraper"
        os.makedirs(base_tmp_dir, exist_ok=True)

        # Create a unique subdirectory for this run
        execution_id = uuid.uuid4().hex
        output_dir = os.path.join(base_tmp_dir, f"extract_{execution_id}")
        os.makedirs(output_dir, exist_ok=True)

        results = []  # will store tuples of (list_of_dfs, chosen_header)
        header_usage = {}

        try:
            # 1) Parallel process all URLs
            with ThreadPoolExecutor(max_workers=min(16, os.cpu_count() or 4)) as executor:
                future_to_url = {
                    executor.submit(self.fetch_and_extract, url): url for url in urls
                }
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        dfs, header = future.result()
                        if dfs is not None:
                            results.append((dfs, header))
                            if header:
                                header_tuple = tuple(header)
                                header_usage[header_tuple] = header_usage.get(header_tuple, 0) + 1
                    except Exception as e:
                        print(f"Error processing PDF: {url}, Error: {e}")

            # 2) Determine the globally most-used header
            if header_usage:
                global_most_used_header_tuple, global_freq = max(
                    header_usage.items(),
                    key=lambda x: x[1]
                )
                global_most_used_header = list(global_most_used_header_tuple)
                print(f"Global most-used header: {global_most_used_header} (used {global_freq} times)")
            else:
                global_most_used_header = None

            # 3) Reassign fallback headers to the global header where applicable
            all_dfs = []
            for (dfs, chosen_header) in results:
                if not dfs:
                    continue

                # If there's a global header and it differs from chosen_header
                # but they share the same column count, unify columns to the global
                if (
                    global_most_used_header is not None
                    and chosen_header != global_most_used_header
                    and len(chosen_header) == len(global_most_used_header)
                ):
                    for df in dfs:
                        df.columns = global_most_used_header

                all_dfs.extend(dfs)

            # 4) Final merge and cleanup
            if all_dfs:
                final_df = pd.concat(all_dfs, ignore_index=True)

                # --- Remove entirely blank rows (including empty strings) ---
                final_df.replace('', pd.NA, inplace=True)
                final_df.dropna(how='all', inplace=True)

                # --- Remove rows that look like repeated headers ---
                def row_starts_like_header(row, col_headers):
                    """
                    Returns True if *every* cell in 'row'
                    starts with the first 2 chars of the corresponding header.
                    """
                    for cell_value, col_name in zip(row, col_headers):
                        cell_str = str(cell_value).strip().lower()
                        col_start = str(col_name).strip().lower()[:2]  # first 2 chars
                        if not cell_str.startswith(col_start):
                            return False
                    return True

                header_mask = final_df.apply(
                    lambda r: row_starts_like_header(r, final_df.columns),
                    axis=1
                )
                final_df = final_df[~header_mask]

                # --- Export the final dataframe ---
                buffer = io.BytesIO()
                if output_format == OutputFormat.CSV.value:
                    csv_str = final_df.to_csv(index=False)
                    buffer.write(csv_str.encode("utf-8"))
                    file_extension = "csv"
                    mime_type = "text/csv"
                elif output_format == OutputFormat.PARQUET.value:
                    final_df.to_parquet(buffer, index=False, engine="pyarrow")
                    file_extension = "parquet"
                    mime_type = "application/octet-stream"
                else:
                    return {"error": f"Unsupported output format: {output_format}"}

                buffer.seek(0)
                headers = {
                    "Content-Disposition": f'attachment; filename="final_extracted_data.{file_extension}"'
                }
                return buffer, mime_type, headers
            else:
                print("No valid tables were extracted from any PDF.")
                return None
        finally:
            # Safely remove the temporary directory in /tmp/web_scraper
            shutil.rmtree(output_dir, ignore_errors=True)
