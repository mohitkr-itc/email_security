import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd

from services.logging_service import get_service_logger

logger = get_service_logger("dataset_stats")


class DatasetStatisticsGenerator:
    """
    Generates statistics and metadata reports for datasets loaded by the DatasetLoader.
    """

    def __init__(self):
        self.report: Dict[str, Any] = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "datasets": {}
        }

    def _extract_dataframe_stats(self, df: pd.DataFrame, dataset_name: str, has_labels: bool = True) -> Dict[str, Any]:
        """
        Extract tabular statistics from a DataFrame based dataset (e.g., URLs, IOCs).
        """
        stats = {
            "type": "tabular",
            "samples": len(df),
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
        }

        # Check for label distribution
        label_col = next((col for col in ['label', 'class', 'type'] if col in df.columns), None)
        if label_col:
            stats["label_distribution"] = df[label_col].value_counts().to_dict()
        else:
            stats["label_distribution"] = "No label column found."
            
        # Optional: memory usage for very large datasets
        stats["memory_usage_mb"] = float(df.memory_usage(deep=True).sum() / (1024 * 1024))
        
        return stats

    def _extract_file_collection_stats(self, files: List[Path], dataset_type: str) -> Dict[str, Any]:
        """
        Extract statistics for a file-based dataset (e.g., Emails, Attachments).
        """
        extensions = {}
        total_size_bytes = 0

        for f in files:
            ext = f.suffix.lower() if f.suffix else "no_extension"
            extensions[ext] = extensions.get(ext, 0) + 1
            if f.exists():
                total_size_bytes += f.stat().st_size

        stats = {
            "type": "file_collection",
            "samples": len(files),
            "extensions_distribution": extensions,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "missing_values": "N/A for raw file collections."
        }
        return stats

    def generate_stats(self, dataset: Union[pd.DataFrame, List[Path]], dataset_name: str, dataset_type: str) -> None:
        """
        Generates and stores statistics for a given dataset block.
        Args:
            dataset: The actual dataset object (DataFrame or List of Paths).
            dataset_name: Name of the dataset module (e.g. 'urls', 'emails')
            dataset_type: Logical type to assist parser (e.g. 'tabular', 'files')
        """
        logger.info(f"Generating stats for dataset: {dataset_name} ({dataset_type})")
        
        if isinstance(dataset, pd.DataFrame):
            stats = self._extract_dataframe_stats(dataset, dataset_name)
        elif isinstance(dataset, list):
            stats = self._extract_file_collection_stats(dataset, dataset_type)
        else:
            logger.warning(f"Unsupported dataset object type for {dataset_name}. Skipping stats.")
            stats = {"error": "Unsupported dataset type."}

        # Store in internal structure grouped by module name
        self.report["datasets"][dataset_name] = stats
        logger.debug(f"Stats generated for {dataset_name}: {stats}")


    def export_report(self, output_path: str = "dataset_report.json") -> str:
        """
        Exports the aggregated dataset statistics to a JSON file.
        """
        path = Path(output_path)
        
        # Calculate summary across all
        total_samples = 0
        for name, data in self.report["datasets"].items():
            if "samples" in data:
                total_samples += data["samples"]
        
        self.report["summary"] = {
            "total_datasets_loaded": len(self.report["datasets"]),
            "total_samples_aggregate": total_samples
        }

        try:
            with open(path, "w") as f:
                 json.dump(self.report, f, indent=4)
            logger.info(f"Dataset report successfully saved to: {path}")
            return str(path)
        except Exception as e:
            logger.error(f"Failed to save dataset report: {str(e)}")
            return ""
