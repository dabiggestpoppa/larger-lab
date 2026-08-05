"""
Schema detection module for Capital Routing Research System.

This module implements schema detection functionality for data files,
identifying column names, data types, and structure information.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import csv
import os


class SchemaDetector:
    """Schema detection class for the Capital Routing Research System."""
    
    def __init__(self):
        """Initialize the schema detector."""
        self.supported_formats = ['.csv', '.parquet', '.json']
        self.numeric_patterns = [
            r'^\d+$',  # Integer
            r'^\d+\.\d+$',  # Float
            r'^\d+\.\d+e[+-]?\d+$',  # Scientific notation
        ]
        self.date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
            r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
        ]
    
    def detect_schema(self, file_path: str, file_format: str) -> Dict[str, Any]:
        """
        Detect schema of a data file.
        
        Args:
            file_path: Path to the data file
            file_format: Format of the file (csv, parquet, json)
            
        Returns:
            Dictionary containing schema information
        """
        schema_info = {
            'file_path': file_path,
            'file_format': file_format,
            'detected_at': datetime.now().isoformat(),
            'columns': [],
            'data_types': {},
            'sample_data': {},
            'statistics': {},
            'quality_metrics': {},
        }
        
        try:
            if file_format == 'csv':
                self._detect_csv_schema(file_path, schema_info)
            elif file_format == 'parquet':
                self._detect_parquet_schema(file_path, schema_info)
            elif file_format == 'json':
                self._detect_json_schema(file_path, schema_info)
            
            # Calculate statistics
            schema_info['statistics'] = self._calculate_statistics(schema_info)
            
            # Calculate quality metrics
            schema_info['quality_metrics'] = self._calculate_quality_metrics(schema_info)
            
        except Exception as e:
            schema_info['error'] = str(e)
            schema_info['detection_failed'] = True
        
        return schema_info
    
    def _detect_csv_schema(self, file_path: str, schema_info: Dict[str, Any]):
        """
        Detect schema of a CSV file.
        
        Args:
            file_path: Path to the CSV file
            schema_info: Dictionary to populate with schema information
        """
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Extract column information
        for column in df.columns:
            column_info = {
                'name': column,
                'data_type': self._infer_data_type(df[column]),
                'null_count': df[column].isnull().sum(),
                'unique_values': df[column].nunique(),
                'sample_values': self._get_sample_values(df[column]),
            }
            schema_info['columns'].append(column_info)
            schema_info['data_types'][column] = column_info['data_type']
            schema_info['sample_data'][column] = column_info['sample_values']
    
    def _detect_parquet_schema(self, file_path: str, schema_info: Dict[str, Any]):
        """
        Detect schema of a Parquet file.
        
        Args:
            file_path: Path to the Parquet file
            schema_info: Dictionary to populate with schema information
        """
        # Read Parquet file
        df = pd.read_parquet(file_path)
        
        # Extract column information
        for column in df.columns:
            column_info = {
                'name': column,
                'data_type': self._infer_data_type(df[column]),
                'null_count': df[column].isnull().sum(),
                'unique_values': df[column].nunique(),
                'sample_values': self._get_sample_values(df[column]),
            }
            schema_info['columns'].append(column_info)
            schema_info['data_types'][column] = column_info['data_type']
            schema_info['sample_data'][column] = column_info['sample_values']
    
    def _detect_json_schema(self, file_path: str, schema_info: Dict[str, Any]):
        """
        Detect schema of a JSON file.
        
        Args:
            file_path: Path to the JSON file
            schema_info: Dictionary to populate with schema information
        """
        # Read JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Array of objects
            if data:
                first_item = data[0]
                if isinstance(first_item, dict):
                    for key, value in first_item.items():
                        column_info = {
                            'name': key,
                            'data_type': self._infer_json_value_type(value),
                            'null_count': sum(1 for item in data if key not in item or item[key] is None),
                            'unique_values': len(set(item.get(key) for item in data if key in item)),
                            'sample_values': self._get_json_sample_values(data, key),
                        }
                        schema_info['columns'].append(column_info)
                        schema_info['data_types'][key] = column_info['data_type']
                        schema_info['sample_data'][key] = column_info['sample_values']
        
        elif isinstance(data, dict):
            # Object
            for key, value in data.items():
                column_info = {
                    'name': key,
                    'data_type': self._infer_json_value_type(value),
                    'null_count': 0,  # Simplified for single object
                    'unique_values': 1,  # Simplified for single object
                    'sample_values': [value],
                }
                schema_info['columns'].append(column_info)
                schema_info['data_types'][key] = column_info['data_type']
                schema_info['sample_data'][key] = column_info['sample_values']
    
    def _infer_data_type(self, series) -> str:
        """
        Infer data type of a pandas Series.
        
        Args:
            series: Pandas Series to analyze
            
        Returns:
            String indicating inferred data type
        """
        # Check for numeric types
        if pd.api.types.is_numeric_dtype(series):
            # Check if it's integer or float
            if series.dtype == 'int64' or series.dtype == 'int32':
                return 'integer'
            elif series.dtype == 'float64' or series.dtype == 'float32':
                return 'float'
            else:
                return 'numeric'
        
        # Check for datetime types
        elif pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        
        # Check for boolean types
        elif pd.api.types.is_bool_dtype(series):
            return 'boolean'
        
        # Check for string/object types
        elif pd.api.types.is_string_dtype(series):
            # Try to infer if it's a date string
            sample = series.dropna().head(10)
            if len(sample) > 0:
                date_count = sum(1 for val in sample if self._is_date_string(str(val)))
                if date_count > len(sample) * 0.7:
                    return 'date'
            
            # Try to infer if it's a categorical
            if series.nunique() < len(series) * 0.1:  # Less than 10% unique values
                return 'categorical'
            
            return 'string'
        
        # Default to object
        else:
            return 'object'
    
    def _infer_json_value_type(self, value: Any) -> str:
        """
        Infer data type of a JSON value.
        
        Args:
            value: JSON value to analyze
            
        Returns:
            String indicating inferred data type
        """
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            if self._is_date_string(value):
                return 'date'
            else:
                return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'unknown'
    
    def _is_date_string(self, value: str) -> bool:
        """
        Check if a string is a date.
        
        Args:
            value: String to check
            
        Returns:
            True if string is a date, False otherwise
        """
        import re
        from datetime import datetime
        
        # Check for common date patterns
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
            r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, value):
                try:
                    # Try to parse the date
                    if pattern == r'^\d{4}-\d{2}-\d{2}$':
                        datetime.strptime(value, '%Y-%m-%d')
                    elif pattern == r'^\d{2}/\d{2}/\d{4}$':
                        datetime.strptime(value, '%m/%d/%Y')
                    elif pattern == r'^\d{2}-\d{2}-\d{4}$':
                        datetime.strptime(value, '%d-%m-%Y')
                    elif pattern == r'^\d{4}/\d{2}/\d{2}$':
                        datetime.strptime(value, '%Y/%m/%d')
                    return True
                except ValueError:
                    pass
        
        return False
    
    def _get_sample_values(self, series) -> List[Any]:
        """
        Get sample values from a pandas Series.
        
        Args:
            series: Pandas Series to sample from
            
        Returns:
            List of sample values
        """
        # Get up to 5 sample values
        sample = series.dropna().head(5).tolist()
        return sample
    
    def _get_json_sample_values(self, data: List[Dict], key: str) -> List[Any]:
        """
        Get sample values from JSON data for a specific key.
        
        Args:
            data: JSON data (list of dictionaries)
            key: Key to extract values for
            
        Returns:
            List of sample values
        """
        # Get up to 5 sample values
        sample = []
        for item in data:
            if key in item and item[key] is not None:
                sample.append(item[key])
                if len(sample) >= 5:
                    break
        
        return sample
    
    def _calculate_statistics(self, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate statistics from schema information.
        
        Args:
            schema_info: Schema information
            
        Returns:
            Dictionary containing statistics
        """
        statistics = {
            'total_columns': len(schema_info['columns']),
            'numeric_columns': 0,
            'datetime_columns': 0,
            'string_columns': 0,
            'categorical_columns': 0,
            'null_columns': 0,
            'total_rows': 0,
        }
        
        # Calculate column statistics
        for column_info in schema_info['columns']:
            data_type = column_info['data_type']
            if data_type in ['integer', 'float', 'numeric', 'date']:
                statistics['numeric_columns'] += 1
            if data_type in ['datetime', 'date']:
                statistics['datetime_columns'] += 1
            elif data_type == 'string':
                statistics['string_columns'] += 1
            elif data_type == 'categorical':
                statistics['categorical_columns'] += 1
            
            if column_info['null_count'] > 0:
                statistics['null_columns'] += 1
        
        return statistics
    
    def _calculate_quality_metrics(self, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality metrics from schema information.
        
        Args:
            schema_info: Schema information
            
        Returns:
            Dictionary containing quality metrics
        """
        quality_metrics = {
            'completeness': 0.0,
            'uniqueness': 0.0,
            'validity': 0.0,
            'overall_score': 0.0,
        }
        
        if schema_info['columns']:
            # Calculate completeness (percentage of non-null values)
            total_values = 0
            non_null_values = 0
            for column_info in schema_info['columns']:
                # This would need actual data to calculate properly
                # For now, use placeholder values
                total_values += 1000  # Placeholder
                non_null_values += 1000 - column_info['null_count']
            
            if total_values > 0:
                quality_metrics['completeness'] = non_null_values / total_values
            
            # Calculate uniqueness (average uniqueness across columns)
            uniqueness_scores = []
            for column_info in schema_info['columns']:
                if len(column_info['sample_values']) > 0:
                    uniqueness_scores.append(column_info['unique_values'] / len(column_info['sample_values']))
            
            if uniqueness_scores:
                quality_metrics['uniqueness'] = sum(uniqueness_scores) / len(uniqueness_scores)
            
            # Calculate overall score
            quality_metrics['overall_score'] = (
                quality_metrics['completeness'] * 0.4 +
                quality_metrics['uniqueness'] * 0.3 +
                quality_metrics['validity'] * 0.3
            )
        
        return quality_metrics