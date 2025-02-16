docker build -t web-scraper .
docker run -d -p 8000:8000 web-scraper


# Don't forget examples

curl -X POST "http://127.0.0.1:8000/files/discover" -H "Content-Type: application/json" -d '{"url":"https://www.pa.gov/agencies/dli/programs-services/workers-compensation/wc-health-care-services-review/wc-fee-schedule/part-b-fee-schedules.html","file_type":"pdf","data_type":"tables","css_selector":"#container-6a16e9c289 > div > div.columncontrol.aem-GridColumn.aem-GridColumn--default--12"}' --output pdf_urls.json


curl -X POST "http://127.0.0.1:8000/files/extract" -H "Content-Type: application/json" -d '{"document_urls":["https://www.pa.gov/content/dam/copapwp-pagov/en/dli/documents/businesses/compensation/wc/hcsr/medfeereview/fee-schedule/documents/part-b/31636-33211.pdf"],"data_type":"tables","output_format":"csv"}' --output extracted_data_single.csv


curl -X POST "http://127.0.0.1:8000/files/collect" -H "Content-Type: application/json" -d '{"discover":{"url":"https://www.pa.gov/agencies/dli/programs-services/workers-compensation/wc-health-care-services-review/wc-fee-schedule/part-b-fee-schedules.html","type":"pdf","data_type":"tables","css_selector":"#container-6a16e9c289 > div > div.columncontrol.aem-GridColumn.aem-GridColumn--default--12"},"extract":{"data_type":"tables","output_format":"csv"}}' --output downloaded_file.csv