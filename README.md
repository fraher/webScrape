# Web Scraper Application

This API application is a web scraper and document extrator built with FastAPI, beautifulsoup4, and pdfplumber that pulls data from PDF files found on web pages. It supports extracting tables of a similar structure from one or more PDFs and returns the data in a single CSV or Parquet format. 

## Getting Started

### Prerequisites

- Python 3.10
- Docker (optional, for containerized deployment)

### Installation (Local Environment)

1. Clone the repository:
    ```sh
    git clone https://github.com/fraher/webScrape.git
    cd web-scraper
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3.10 -m venv venv
    source venv/bin/activate
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

### Running the Application

To run the application locally, use the following command:
```sh
uvicorn app.main:app --reload
```

The application will be accessible at `http://127.0.0.1:8000`.

### Building and Running with Docker

1. Build the Docker image:
    ```sh
    docker build -t web-scraper .
    ```

2. Run the Docker container:
    ```sh
    docker run -d -p 8000:8000 web-scraper
    ```

The application will be accessible at `http://127.0.0.1:8000`.

### API Documentation

Once the application is running, you can access the Swagger UI for API documentation and testing at `http://127.0.0.1:8000/docs`.

## API Endpoints

### Discover PDF Files

Discover PDF files on a webpage and return their URLs.

#### Parameters:

- **URL:** The page to be evaluted for a specific type of linked files, in this case we will search "PDFs"

- **Type:** The default type of file that will be searched for, at this time only "pdf" is supported (Unsupported type error will be returend if another type is *specified)

- **Data_Type:** The default data structure of information to be searched for and returned, in this case 'tables" with the type (e.g., PDFs). At this time only "tables" is supported (Unsupported type error will be returend if another type is *specified)

- **CSS_Selector:** This optional value is a direct css selector path on the web page to the element which contains the data_type (e.g., PDFs)

#### Call:
- **Endpoint:** `/files/discover`
- **Method:** `POST`
- **Request Body:**
    ```json
    {
        "url": "https://example.com/page-with-pdfs",
        "type": "pdf",
        "data_type": "tables",
        "css_selector": "#container > div > a"
    }
    ```
- **Response:**
    ```json
    {
        "document_urls": ["https://example.com/file1.pdf", "https://example.com/file2.pdf"]
    }
    ```

### Extract Tables from PDF Files

Extract tables from PDF files given a list of URLs.

#### Parameters:
- **Document_Urls:** A list of PDF link URLs to be read and tables extracted. (This will accept the direct key/ value list output from the discover method above)
- **Data_Type:** The default data structure of information to be searched for and returned, in this case 'tables" with the type (e.g., PDFs). At this time only "tables" is supported (Unsupported type error will be returend if another type is *specified)
- **Output_Format:** Specify if you will be downloading a final CSV file or Parquet file.

#### Call:
- **Endpoint:** `/files/extract`
- **Method:** `POST`
- **Request Body:**
    ```json
    {
        "document_urls": ["https://example.com/file1.pdf"],
        "data_type": "tables",
        "output_format": "csv"
    }
    ```
- **Response:** Returns a CSV or Parquet file with the extracted data.

### Discover and Extract Tables

Discover PDF files on a webpage and extract tables from them.

#### Parameters:

- **URL:** The page to be evaluted for a specific type of linked files, in this case we will search "PDFs"

- **Type:** The default type of file that will be searched for, at this time only "pdf" is supported (Unsupported type error will be returend if another type is *specified)

- **Data_Type:** The default data structure of information to be searched for and returned, in this case 'tables" with the type (e.g., PDFs). At this time only "tables" is supported (Unsupported type error will be returend if another type is *specified)

- **CSS_Selector:** This optional value is a direct css selector path on the web page to the element which contains the data_type (e.g., PDFs)

- **Document_Urls:** A list of PDF link URLs to be read and tables extracted. (This will accept the direct key/ value list output from the discover method above)
- **Data_Type:** The default data structure of information to be searched for and returned, in this case 'tables" with the type (e.g., PDFs). At this time only "tables" is supported (Unsupported type error will be returend if another type is *specified)
- **Output_Format:** Specify if you will be downloading a final CSV file or Parquet file.

#### Call
- **Endpoint:** `/files/collect`
- **Method:** `POST`
- **Request Body:**
    ```json
    {
        "discover": {
            "url": "https://example.com/page-with-pdfs",
            "type": "pdf",
            "data_type": "tables",
            "css_selector": "#container > div > a"
        },
        "extract": {
            "data_type": "tables",
            "output_format": "csv"
        }
    }
    ```
- **Response:** Returns a CSV or Parquet file with the extracted data.

## cURL Examples

### Discover PDF Files
```sh
curl -X POST "http://127.0.0.1:8000/files/discover" -H "Content-Type: application/json" -d '{"url":"https://example.com/page-with-pdfs","type":"pdf","data_type":"tables","css_selector":"#container > div > a"}'
```

### Extract Tables from PDF Files
```sh
curl -X POST "http://127.0.0.1:8000/files/extract" -H "Content-Type: application/json" -d '{"document_urls":["https://example.com/file1.pdf"],"data_type":"tables","output_format":"csv"}' --output extracted_data.csv
```

### Discover and Extract Tables
```sh
curl -X POST "http://127.0.0.1:8000/files/collect" -H "Content-Type: application/json" -d '{"discover":{"url":"https://example.com/page-with-pdfs","type":"pdf","data_type":"tables","css_selector":"#container > div > a"},"extract":{"data_type":"tables","output_format":"csv"}}' --output collected_data.csv
```


## Requirements

The application dependencies are listed in the `requirements.txt` file:
```txt
docopt==0.6.2
fastapi==0.115.8
fqdn==1.5.1
isoduration==20.11.0
jsonpointer==3.0.0
pandas==2.2.3
pdfplumber==0.11.5
pytest==8.3.4
tinycss2==1.4.0
uri-template==1.3.0
uvicorn==0.34.0
webcolors==24.11.1
yarg==0.1.9
beautifulsoup4==4.13.3
pyarrow==19.0.0
```

### Testing Instructions
To run the pytests for this project, follow these steps:

1. Ensure you have installed the required dependencies, including `pytest`, by running:
    ```sh
    pip install -r requirements.txt
    ```

2. Activate your virtual environment if it's not already activated:
    ```sh
    source venv/bin/activate
    ```

3. Run the tests using the `pytest` command in the parent folder:
    ```sh
    pytest
    ```

This will automatically discover and execute all the test cases defined in the project. The test results will be displayed in the terminal, showing which tests passed and which failed.

The .vscode folder has also been configured with settings.json to enable testing within the IDE.

## Future Directions
### Cloud Storage & File Caching
Implementing online blob storage would provide a standardized way to store exports, enabling users to download them anytime from any location.

Currently, the software downloads each PDF upon request for extraction. Future iterations could cache previously downloaded files in cloud storage, reducing latency by keeping them closer to the processing application. This would also decrease the number of download requests sent to the host server.

### Background Processing & Asynchronous Operations
The current API processes PDF extractions synchronously, which is time-consuming. Each PDF is loaded into memory, processed, and returned within a single request. This approach keeps the API call open for up to 10 minutes when processing ~80 PDFs, which is excessive.

A future enhancement would introduce an asynchronous processing model, where each extraction request is assigned a unique ID. Additional API endpoints could allow users to check extraction status and retrieve results upon completion. Cloud storage, as described earlier, would store the outputs, and an optional email notification could alert stakeholders once processing is complete.

### Automated Deployment
Implementing CI/CD for production deployment would accelerate time-to-market and streamline prototyping. Integrating GitHub Actions for automated deployments to a cloud server would be a key next step. Since the application is containerized, deploying as an Azure Container App would be a viable option.

### Enhanced Logging
Currently, logging is limited to console output. Implementing a structured logging framework would improve visibility, making debugging and monitoring more effective.

### Additional Types & Targets
Expanding the range of supported file types and extraction targets would enhance the flexibility and applicability of the system.

#### Additional File Types
Currently, the system supports PDF extraction, but extending support to other common document formats—such as DOCX, CSV, TXT, and HTML—would allow for broader use cases. Each format may require specialized parsing logic to ensure accurate data extraction.

#### Expanded Extraction Targets
Beyond text and tables, additional document elements could be extracted to meet diverse user needs. Future iterations could support:

##### Tables: Enhanced detection and extraction from structured documents.
##### Divs & Sections: Capturing segmented content from web pages and reports.
##### Images & Diagrams: Extracting embedded images with metadata or processing them with OCR for text extraction.

### Large Multimodal Models
Integrating large multimodal models would enable the system to process and analyze diverse data types, such as text, images, and audio, simultaneously, enhancing its overall capability and performance. Additionally they could provide direct extraction or support to existing processes.

Incorporating these enhancements would improve the system’s versatility, making it more adaptable to various document processing workflows.

## Conclusion

This web scraper application is designed to help you extract data from PDF files found on web pages. With the provided API endpoints and examples, you can easily get started and integrate this functionality into your projects. For more details, refer to the Swagger UI documentation available at `http://127.0.0.1:8000/docs`.