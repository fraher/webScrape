from enum import Enum

class FileType(Enum):
    PDF = "pdf"
    # Add more file types here

class DataType(Enum):
    Tables = "tables"
    # Add more data structures here

class OutputFormat(Enum):
    CSV = "csv"    
    PARQUET = "parquet"
    # Add more output formats here