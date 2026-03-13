import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from datasets.dataset_validator import DatasetValidator
from services.logging_service import get_service_logger

logger = get_service_logger("dataset_loader")


class DatasetLoader:
    """
    Handles the ingestion and loading of diverse cybersecurity datasets.
    It utilizes the DatasetValidator to ensure structural integrity.
    """

    def __init__(self, base_dataset_dir: str = "datasets"):
        self.base_dir = Path(base_dataset_dir)
        self.validator = DatasetValidator()

    def load_email_dataset(self, source_dir: str = "email_content") -> Dict[str, Any]:
        """
        Loads the email corpus dataset (e.g., Enron, SpamAssassin, Nazario).
        Returns a dictionary containing a list of file paths and validation details.
        """
        dataset_path = self.base_dir / source_dir
        logger.info(f"Loading email dataset from: {dataset_path}")

        is_valid, files, details = self.validator.validate_email_format(dataset_path)

        if not is_valid:
            logger.error(f"Email dataset validation failed: {details.get('error')}")
            return {"status": "error", "details": details, "data": []}

        # For a production system, we might yield files or map them to an index.
        # Here we return the list of paths for the agent to process incrementally.
        logger.info(f"Successfully loaded email dataset. Found {len(files)} files.")
        return {"status": "success", "details": details, "data": files}

    def load_url_dataset(self, source_dir: str = "url_dataset") -> Dict[str, Any]:
        """
        Loads the URL dataset (e.g., PhishTank, OpenPhish).
        Expects CSV files within the directory.
        """
        dataset_path = self.base_dir / source_dir
        logger.info(f"Loading URL dataset from: {dataset_path}")
        
        all_dataframes = []
        all_details = []

        if not dataset_path.exists() or not dataset_path.is_dir():
            logger.error(f"URL dataset directory not found: {dataset_path}")
            return {"status": "error", "details": f"Directory not found: {dataset_path}", "data": None}

        # Scan for CSV files inside the directory
        csv_files = list(dataset_path.rglob("*.csv"))
        
        if not csv_files:
            logger.warning(f"No CSV files found in URL dataset directory {dataset_path}")
            return {"status": "warning", "details": "No CSV files found. Empty dataset.", "data": pd.DataFrame()}
            
        for file_path in csv_files:
            is_valid, df, details = self.validator.validate_url_format(file_path)
            all_details.append(details)
            if is_valid and df is not None:
                df['source_file'] = file_path.name
                all_dataframes.append(df)
            else:
                 logger.warning(f"Skipping invalid URL dataset file: {file_path}")

        if not all_dataframes:
            return {"status": "error", "details": "All URL dataset files failed validation.", "data": pd.DataFrame()}

        # Concatenate all valid datasets
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        logger.info(f"Successfully loaded URL dataset. Combined shape: {combined_df.shape}")
        return {"status": "success", "details": all_details, "data": combined_df}

    def load_attachment_dataset(self, source_dir: str = "attachments") -> Dict[str, Any]:
        """
        Loads the malware/attachment dataset (e.g., EMBER, MalwareBazaar).
        """
        dataset_path = self.base_dir / source_dir
        logger.info(f"Loading attachment dataset from: {dataset_path}")

        is_valid, files, details = self.validator.validate_attachment_format(dataset_path)

        if not is_valid:
            logger.error(f"Attachment dataset validation failed: {details.get('error')}")
            return {"status": "error", "details": details, "data": []}

        # Similar to emails, return paths for incremental processing/sandbox integration
        logger.info(f"Successfully loaded attachment dataset. Found {len(files)} files.")
        return {"status": "success", "details": details, "data": files}

    def load_ioc_feeds(self, source_dir: str = "threat_intelligence") -> Dict[str, Any]:
        """
        Loads the Threat Intelligence feeds dataset (AbuseIPDB, URLHaus).
        Expects CSV or JSON files.
        """
        dataset_path = self.base_dir / source_dir
        logger.info(f"Loading IOC feeds from: {dataset_path}")
        
        all_dataframes = []
        all_details = []

        if not dataset_path.exists() or not dataset_path.is_dir():
            logger.error(f"IOC dataset directory not found: {dataset_path}")
            return {"status": "error", "details": f"Directory not found: {dataset_path}", "data": None}

        # Scan for CSV/JSON files
        files = list(dataset_path.rglob("*.csv")) + list(dataset_path.rglob("*.json"))

        if not files:
            logger.warning(f"No CSV/JSON files found in IOC dataset directory {dataset_path}")
            return {"status": "warning", "details": "No CSV/JSON files found. Empty dataset.", "data": pd.DataFrame()}

        for file_path in files:
            is_valid, df, details = self.validator.validate_ioc_format(file_path)
            all_details.append(details)
            if is_valid and df is not None:
                df['source_feed'] = file_path.name
                all_dataframes.append(df)
            else:
                logger.warning(f"Skipping invalid IOC feed file: {file_path}")

        if not all_dataframes:
            return {"status": "error", "details": "All IOC feed files failed validation.", "data": pd.DataFrame()}

        combined_df = pd.concat(all_dataframes, ignore_index=True)
        logger.info(f"Successfully loaded IOC feeds. Combined shape: {combined_df.shape}")
        return {"status": "success", "details": all_details, "data": combined_df}
