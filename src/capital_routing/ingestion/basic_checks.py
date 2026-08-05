"""
Basic checks module for Capital Routing Research System.

This module implements basic data quality checks for the Capital Routing
Research System, providing functionality to validate data quality and
identify potential issues.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import os


class BasicChecks:
    """Basic checks class for the Capital Routing Research System."""
    
    def __init__(self):
        """Initialize the basic checks."""
        # Define check thresholds
        self.check_thresholds = {
            'min_rows': 10,
            'max_null_percentage': 50.0,
            'min_unique_values': 1,
            'max_duplicate_percentage': 95.0,
            'min_quality_score': 0.0,
        }
        
        # Define check types
        self.check_types = {
            'completeness': 'Completeness checks',
            'uniqueness': 'Uniqueness checks',
            'validity': 'Validity checks',
            'consistency': 'Consistency checks',
            'timeliness': 'Timeliness checks',
        }
    
    def check_completeness(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data completeness.
        
        Args:
            data: DataFrame to check
            
        Returns:
            Dictionary containing completeness check results
        """
        completeness_results = {
            'check_type': 'completeness',
            'timestamp': datetime.now().isoformat(),
            'total_rows': len(data),
            'total_columns': len(data.columns),
            'null_counts': {},
            'null_percentages': {},
            'completeness_score': 0.0,
            'issues': [],
        }
        
        # Calculate null counts and percentages
        for column in data.columns:
            null_count = data[column].isnull().sum()
            null_percentage = (null_count / len(data)) * 100
            
            completeness_results['null_counts'][column] = int(null_count)
            completeness_results['null_percentages'][column] = float(null_percentage)
            
            # Check for issues
            if null_percentage > self.check_thresholds['max_null_percentage']:
                completeness_results['issues'].append(
                    f"Column '{column}' has {null_percentage:.1f}% null values"
                )
        
        # Calculate completeness score
        total_cells = len(data) * len(data.columns)
        total_null_cells = sum(completeness_results['null_counts'].values())
        
        if total_cells > 0:
            completeness_results['completeness_score'] = (
                (total_cells - total_null_cells) / total_cells
            ) * 100
        
        return completeness_results
    
    def check_uniqueness(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data uniqueness.
        
        Args:
            data: DataFrame to check
            
        Returns:
            Dictionary containing uniqueness check results
        """
        uniqueness_results = {
            'check_type': 'uniqueness',
            'timestamp': datetime.now().isoformat(),
            'total_rows': len(data),
            'unique_rows': len(data.drop_duplicates()),
            'duplicate_percentage': 0.0,
            'unique_counts': {},
            'uniqueness_scores': {},
            'issues': [],
        }
        
        # Calculate duplicate percentage
        unique_rows = len(data.drop_duplicates())
        if len(data) > 0:
            uniqueness_results['duplicate_percentage'] = (
                (len(data) - unique_rows) / len(data)
            ) * 100
        
        # Calculate uniqueness for each column
        for column in data.columns:
            unique_count = data[column].nunique()
            uniqueness_score = (unique_count / len(data)) * 100
            
            uniqueness_results['unique_counts'][column] = int(unique_count)
            uniqueness_results['uniqueness_scores'][column] = float(uniqueness_score)
            
            # Check for issues
            if uniqueness_score < self.check_thresholds['min_unique_values']:
                uniqueness_results['issues'].append(
                    f"Column '{column}' has low uniqueness ({uniqueness_score:.1f}%)"
                )
        
        return uniqueness_results
    
    def check_validity(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data validity.
        
        Args:
            data: DataFrame to check
            
        Returns:
            Dictionary containing validity check results
        """
        validity_results = {
            'check_type': 'validity',
            'timestamp': datetime.now().isoformat(),
            'total_rows': len(data),
            'valid_rows': 0,
            'validity_score': 0.0,
            'issues': [],
        }
        
        # Check for valid data types
        for column in data.columns:
            # Check for numeric columns
            if pd.api.types.is_numeric_dtype(data[column]):
                # Check for infinite values
                infinite_count = np.isinf(data[column]).sum()
                if infinite_count > 0:
                    validity_results['issues'].append(
                        f"Column '{column}' contains {infinite_count} infinite values"
                    )
                
                # Check for extremely large values
                max_value = data[column].max()
                min_value = data[column].min()
                
                if max_value > 1e10 or min_value < -1e10:
                    validity_results['issues'].append(
                        f"Column '{column}' contains extremely large values (max: {max_value}, min: {min_value})"
                    )
            
            # Check for datetime columns
            elif pd.api.types.is_datetime64_any_dtype(data[column]):
                # Check for unrealistic dates
                min_date = data[column].min()
                max_date = data[column].max()
                
                if min_date.year < 1900 or max_date.year > 2030:
                    validity_results['issues'].append(
                        f"Column '{column}' contains unrealistic dates (min: {min_date}, max: {max_date})"
                    )
            
            # Check for string columns
            elif pd.api.types.is_string_dtype(data[column]):
                # Check for empty strings
                empty_count = (data[column] == '').sum()
                if empty_count > 0:
                    validity_results['issues'].append(
                        f"Column '{column}' contains {empty_count} empty strings"
                    )
        
        # Calculate validity score
        total_checks = len(data.columns) * len(data)
        valid_checks = total_checks - len(validity_results['issues'])
        
        if total_checks > 0:
            validity_results['validity_score'] = (valid_checks / total_checks) * 100
        
        return validity_results
    
    def check_consistency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data consistency.
        
        Args:
            data: DataFrame to check
            
        Returns:
            Dictionary containing consistency check results
        """
        consistency_results = {
            'check_type': 'consistency',
            'timestamp': datetime.now().isoformat(),
            'total_rows': len(data),
            'consistent_rows': 0,
            'consistency_score': 0.0,
            'issues': [],
        }
        
        # Check for consistent data types across columns
        for column in data.columns:
            # Check for mixed data types
            if pd.api.types.is_object_dtype(data[column]):
                # Try to infer data type
                sample = data[column].dropna().head(10)
                if len(sample) > 0:
                    # Check if all values are strings
                    if all(isinstance(val, str) for val in sample):
                        continue
                    
                    # Check if all values are numeric
                    if all(isinstance(val, (int, float)) for val in sample):
                        continue
                    
                    # Check if all values are dates
                    if all(isinstance(val, datetime) for val in sample):
                        continue
                    
                    # Mixed data types detected
                    consistency_results['issues'].append(
                        f"Column '{column}' contains mixed data types"
                    )
        
        # Check for consistent formatting
        for column in data.columns:
            if pd.api.types.is_string_dtype(data[column]):
                # Check for inconsistent formatting
                sample = data[column].dropna().head(10)
                if len(sample) > 0:
                    # Check for inconsistent casing
                    if any(val.isupper() for val in sample) and any(val.islower() for val in sample):
                        consistency_results['issues'].append(
                            f"Column '{column}' contains inconsistent casing"
                        )
                    
                    # Check for inconsistent spacing
                    if any(val.startswith(' ') for val in sample) and any(val.endswith(' ') for val in sample):
                        consistency_results['issues'].append(
                            f"Column '{column}' contains inconsistent spacing"
                        )
        
        # Calculate consistency score
        total_checks = len(data.columns) * len(data)
        valid_checks = total_checks - len(consistency_results['issues'])
        
        if total_checks > 0:
            consistency_results['consistency_score'] = (valid_checks / total_checks) * 100
        
        return consistency_results
    
    def check_timeliness(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data timeliness.
        
        Args:
            data: DataFrame to check
            
        Returns:
            Dictionary containing timeliness check results
        """
        timeliness_results = {
            'check_type': 'timeliness',
            'timestamp': datetime.now().isoformat(),
            'total_rows': len(data),
            'timeliness_score': 0.0,
            'issues': [],
        }
        
        # Check for recent data
        for column in data.columns:
            if pd.api.types.is_datetime64_any_dtype(data[column]):
                # Get current date
                current_date = datetime.now()
                
                # Check for outdated data
                max_date = data[column].max()
                days_old = (current_date - max_date).days
                
                if days_old > 365:  # More than 1 year old
                    timeliness_results['issues'].append(
                        f"Column '{column}' contains data older than 1 year (max date: {max_date})"
                    )
                
                # Calculate timeliness score
                timeliness_score = max(0, 100 - (days_old / 365) * 100)
                timeliness_results['timeliness_score'] = timeliness_score
        
        return timeliness_results
    
    def run_all_checks(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run all basic checks.
        
        Args:
            data: DataFrame to check
            
        Returns:
            Dictionary containing all check results
        """
        check_results = {
            'timestamp': datetime.now().isoformat(),
            'total_rows': len(data),
            'total_columns': len(data.columns),
            'checks': {},
            'overall_score': 0.0,
            'issues': [],
        }
        
        # Run all checks
        check_results['checks']['completeness'] = self.check_completeness(data)
        check_results['checks']['uniqueness'] = self.check_uniqueness(data)
        check_results['checks']['validity'] = self.check_validity(data)
        check_results['checks']['consistency'] = self.check_consistency(data)
        check_results['checks']['timeliness'] = self.check_timeliness(data)
        
        # Calculate overall score
        scores = []
        for check_name, check_result in check_results['checks'].items():
            if 'score' in check_result:
                scores.append(check_result['score'])
            # Handle uniqueness check which uses 'uniqueness_scores' dict
            elif 'uniqueness_scores' in check_result:
                # Calculate average uniqueness score across all columns
                uniqueness_scores = list(check_result['uniqueness_scores'].values())
                if uniqueness_scores:
                    avg_uniqueness = sum(uniqueness_scores) / len(uniqueness_scores)
                    scores.append(avg_uniqueness)
        
        if scores:
            check_results['overall_score'] = sum(scores) / len(scores)
        
        # Collect all issues
        for check_name, check_result in check_results['checks'].items():
            if 'issues' in check_result:
                check_results['issues'].extend(check_result['issues'])
        
        return check_results
    
    def generate_check_report(self, check_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a check report.
        
        Args:
            check_results: Check results
            
        Returns:
            Dictionary containing check report
        """
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'total_rows': check_results['total_rows'],
            'total_columns': check_results['total_columns'],
            'overall_score': check_results['overall_score'],
            'total_issues': len(check_results['issues']),
            'check_summary': {},
            'recommendations': [],
        }
        
        # Generate check summary
        for check_name, check_result in check_results['checks'].items():
            report['check_summary'][check_name] = {
                'score': check_result.get('score', 0.0),
                'issues': len(check_result.get('issues', [])),
            }
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(check_results)
        
        return report
    
    def _generate_recommendations(self, check_results: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on check results.
        
        Args:
            check_results: Check results
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for completeness issues
        completeness_issues = check_results['checks']['completeness'].get('issues', [])
        if completeness_issues:
            recommendations.append(
                "Address completeness issues: " + "; ".join(completeness_issues)
            )
        
        # Check for uniqueness issues
        uniqueness_issues = check_results['checks']['uniqueness'].get('issues', [])
        if uniqueness_issues:
            recommendations.append(
                "Address uniqueness issues: " + "; ".join(uniqueness_issues)
            )
        
        # Check for validity issues
        validity_issues = check_results['checks']['validity'].get('issues', [])
        if validity_issues:
            recommendations.append(
                "Address validity issues: " + "; ".join(validity_issues)
            )
        
        # Check for consistency issues
        consistency_issues = check_results['checks']['consistency'].get('issues', [])
        if consistency_issues:
            recommendations.append(
                "Address consistency issues: " + "; ".join(consistency_issues)
            )
        
        # Check for timeliness issues
        timeliness_issues = check_results['checks']['timeliness'].get('issues', [])
        if timeliness_issues:
            recommendations.append(
                "Address timeliness issues: " + "; ".join(timeliness_issues)
            )
        
        # Check for overall score
        if check_results['overall_score'] < self.check_thresholds['min_quality_score']:
            recommendations.append(
                f"Overall quality score is below threshold ({check_results['overall_score']:.1f}% < {self.check_thresholds['min_quality_score']}%)"
            )
        
        return recommendations
    
    def export_check_results(self, check_results: Dict[str, Any], output_path: str):
        """
        Export check results to file.
        
        Args:
            check_results: Check results
            output_path: Path to output file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export to JSON
        with open(output_path, 'w') as f:
            json.dump(check_results, f, indent=2, default=str)
    
    def import_check_results(self, input_path: str) -> Dict[str, Any]:
        """
        Import check results from file.
        
        Args:
            input_path: Path to input file
            
        Returns:
            Dictionary containing check results
        """
        # Import from JSON
        with open(input_path, 'r') as f:
            check_results = json.load(f)
        
        return check_results