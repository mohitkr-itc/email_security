import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from pydantic import BaseModel, ValidationError

from services.logging_service import get_service_logger

logger = get_service_logger("dataset_validator")

# Define Data Schemas (if needed for strict tabular validations)
class EmailMetadataSchema(BaseModel):
    subject: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    date: Optional[str] = None

class URLSchema(BaseModel):
    url: str
    label: Optional[Union[str, int]] = None

class ThreatIntelSchema(BaseModel):
    indicator: str
    type: str # e.g., 'ip', 'domain', 'url'
    source: str

class DatasetValidator:
    """
    Validates datasets (files and directories) before ingestion by the loader.
    """

    @staticmethod
    def _check_missing_values(df: pd.DataFrame) -> Dict[str, int]:
        """
        Check and return missing values count for each column in a DataFrame.
        """
        return df.isnull().sum().to_dict()

    @staticmethod
    def validate_csv(file_path: Union[str, Path], required_columns: Optional[List[str]] = None) -> Tuple[bool, Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Validates a CSV file.
        Returns:
            (is_valid, dataframe_or_none, validation_details)
        """
        path = Path(file_path)
        details = {"file": str(path), "type": "csv", "error": None, "missing_values": {}}
        
        if not path.exists() or not path.is_file():
            details["error"] = "File not found or is not a file."
            logger.error(f"Validation failed: {details['error']} - {path}")
            return False, None, details

        try:
            df = pd.read_csv(path)
            
            if required_columns:
                missing_cols = [col for col in required_columns if col not in df.columns]
                if missing_cols:
                    details["error"] = f"Missing required columns: {missing_cols}"
                    logger.warning(f"Validation failed for {path}: {details['error']}")
                    return False, None, details
            
            details["missing_values"] = DatasetValidator._check_missing_values(df)
            details["shape"] = df.shape
            logger.debug(f"Validated CSV {path} successfully. Shape: {df.shape}")
            return True, df, details

        except Exception as e:
            details["error"] = f"Error reading CSV: {str(e)}"
            logger.error(f"Validation failed for {path}: {details['error']}")
            return False, None, details

    @staticmethod
    def validate_json(file_path: Union[str, Path]) -> Tuple[bool, Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Validates a JSON file.
        Returns:
            (is_valid, dataframe_or_none, validation_details)
        """
        path = Path(file_path)
        details = {"file": str(path), "type": "json", "error": None, "missing_values": {}}

        if not path.exists() or not path.is_file():
            details["error"] = "File not found or is not a file."
            logger.error(f"Validation failed: {details['error']} - {path}")
            return False, None, details

        try:
            # Try to read as records line by line first, then standard json
            try:
                df = pd.read_json(path, lines=True)
            except ValueError:
                df = pd.read_json(path)
            
            details["missing_values"] = DatasetValidator._check_missing_values(df)
            details["shape"] = df.shape
            logger.debug(f"Validated JSON {path} successfully. Shape: {df.shape}")
            return True, df, details

        except Exception as e:
            details["error"] = f"Error reading JSON: {str(e)}"
            logger.error(f"Validation failed for {path}: {details['error']}")
            return False, None, details

    @staticmethod
    def validate_email_format(directory_path: Union[str, Path]) -> Tuple[bool, List[Path], Dict[str, Any]]:
        """
        Validates a directory containing raw email (.eml or .txt) files.
        Returns:
            (is_valid, list_of_valid_files, validation_details)
        """
        path = Path(directory_path)
        details = {"directory": str(path), "type": "email_corpus", "error": None, "total_files": 0, "valid_files": 0}
        
        if not path.exists() or not path.is_dir():
            details["error"] = "Directory not found."
            logger.error(f"Validation failed: {details['error']} - {path}")
            return False, [], details

        # Assume emails are either .eml or .txt. Or no extension (Enron style)
        files = []
        for p in path.rglob("*"):
            if p.is_file():
                # Basic check: just collect all files, advanced parsing is left to loader/extractor
                files.append(p)
                
        details["total_files"] = len(files)
        details["valid_files"] = len(files) # For now, all files are considered "valid" candidates
        
        if len(files) == 0:
             logger.warning(f"Email directory {path} is empty.")
             
        logger.debug(f"Validated Email corpus {path}. Found {len(files)} files.")
        return True, files, details

    @staticmethod
    def validate_url_format(file_path: Union[str, Path]) -> Tuple[bool, Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Validates a URL dataset (usually CSV).
        """
        return DatasetValidator.validate_csv(file_path, required_columns=['url'])

    @staticmethod
    def validate_attachment_format(directory_path: Union[str, Path]) -> Tuple[bool, List[Path], Dict[str, Any]]:
        """
        Validates a directory containing raw malware/attachment samples.
        """
        path = Path(directory_path)
        details = {"directory": str(path), "type": "attachments", "error": None, "total_files": 0}
        
        if not path.exists() or not path.is_dir():
            details["error"] = "Directory not found."
            logger.error(f"Validation failed: {details['error']} - {path}")
            return False, [], details
            
        files = [p for p in path.rglob("*") if p.is_file()]
        details["total_files"] = len(files)
        
        if len(files) == 0:
            logger.warning(f"Attachment directory {path} is empty.")
            
        logger.debug(f"Validated attachment directory {path}. Found {len(files)} files.")
        return True, files, details

    @staticmethod
    def validate_ioc_format(file_path: Union[str, Path]) -> Tuple[bool, Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Validates an IOC (Indicator of Compromise) threat intel dataset.
        Defaults to CSV check, could be expanded for JSON/MISP format.
        """
        path = Path(file_path)
        if path.suffix.lower() == '.json':
            return DatasetValidator.validate_json(path)
        else:
            return DatasetValidator.validate_csv(path)
