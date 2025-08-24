"""
Data cleaning and quality control module for GOQII Health Data EDA Protocol

Implements cleaning rules for all health metrics with quality flagging system.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
import warnings
from scipy import stats
from datetime import timedelta

from .core import HealthDataRecord, HealthDataCollection, BaseProcessor


class QualityFlags:
    """Quality flag constants"""
    GOOD = "good"
    OUTLIER = "outlier" 
    MISSING = "missing"
    INVALID = "invalid"
    DUPLICATE = "duplicate"
    INTERPOLATED = "interpolated"


class HealthDataCleaner(BaseProcessor):
    """
    Main data cleaning processor with metric-specific cleaning rules.
    """
    
    # Validation ranges for each metric type
    VALIDATION_RANGES = {
        'bp': {
            'systolic': (80, 200),
            'diastolic': (50, 130),
        },
        'sleep': {
            'sleep_duration': (0, 24),  # hours
            'sleep_quality': (0, 100),  # score 0-100
        },
        'steps': {
            'step_count': (0, 50000),  # daily steps
            'distance': (0, 100),  # km
        },
        'hr': {
            'heart_rate': (30, 220),  # bpm
            'resting_hr': (30, 120),  # bpm
        },
        'spo2': {
            'spo2': (80, 100),  # percentage
            'confidence': (0, 100),  # confidence score
        },
        'temp': {
            'temperature': (90, 105),  # Fahrenheit
            'ambient_temp': (50, 120),  # Fahrenheit
        }
    }
    
    # Outlier detection parameters
    OUTLIER_PARAMS = {
        'bp': {'z_threshold': 3.0, 'iqr_factor': 2.5},
        'sleep': {'z_threshold': 2.5, 'iqr_factor': 2.0},
        'steps': {'z_threshold': 3.0, 'iqr_factor': 3.0},
        'hr': {'z_threshold': 2.5, 'iqr_factor': 2.0},
        'spo2': {'z_threshold': 2.0, 'iqr_factor': 1.5},
        'temp': {'z_threshold': 2.0, 'iqr_factor': 1.5},
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cleaning_stats = {}
    
    def process(self, data: HealthDataCollection) -> HealthDataCollection:
        """
        Clean all health data in the collection.
        
        Parameters
        ----------
        data : HealthDataCollection
            Collection of raw health data
            
        Returns
        -------
        HealthDataCollection
            Collection with cleaned and flagged data
        """
        self.logger.info("Starting data cleaning process")
        
        cleaned_collection = HealthDataCollection()
        self.cleaning_stats = {}
        
        # Process each metric type separately
        for metric_type in data.get_metric_types():
            self.logger.info(f"Cleaning {metric_type} data")
            
            metric_records = data.get_metric_data(metric_type)
            cleaned_records = self._clean_metric_data(metric_records, metric_type)
            
            cleaned_collection.add_records(cleaned_records)
        
        self._log_cleaning_summary()
        return cleaned_collection
    
    def _clean_metric_data(
        self, 
        records: List[HealthDataRecord], 
        metric_type: str
    ) -> List[HealthDataRecord]:
        """Clean data for a specific metric type"""
        
        if not records:
            return []
        
        # Initialize stats
        self.cleaning_stats[metric_type] = {
            'total_records': len(records),
            'good': 0,
            'outlier': 0,
            'invalid': 0,
            'missing': 0,
            'duplicate': 0,
        }
        
        cleaned_records = []
        
        # Process each participant separately for better outlier detection
        participants = list(set(r.participant_id for r in records))
        
        for participant_id in participants:
            participant_records = [r for r in records if r.participant_id == participant_id]
            
            # Apply cleaning pipeline
            cleaned_participant_records = self._clean_participant_metric_data(
                participant_records, metric_type, participant_id
            )
            
            cleaned_records.extend(cleaned_participant_records)
        
        return cleaned_records
    
    def _clean_participant_metric_data(
        self,
        records: List[HealthDataRecord],
        metric_type: str,
        participant_id: str
    ) -> List[HealthDataRecord]:
        """Clean data for a specific participant and metric"""
        
        # Step 1: Remove duplicates
        records = self._remove_duplicates(records, metric_type)
        
        # Step 2: Sort by datetime
        records.sort(key=lambda x: x.datetime)
        
        # Step 3: Apply validation rules
        records = self._apply_validation_rules(records, metric_type)
        
        # Step 4: Detect outliers
        records = self._detect_outliers(records, metric_type)
        
        # Step 5: Handle missing values (if any interpolation needed)
        records = self._handle_missing_values(records, metric_type)
        
        # Update stats
        for record in records:
            self.cleaning_stats[metric_type][record.quality_flag] += 1
        
        return records
    
    def _remove_duplicates(
        self, 
        records: List[HealthDataRecord], 
        metric_type: str
    ) -> List[HealthDataRecord]:
        """Remove duplicate records based on datetime and values"""
        
        seen = set()
        unique_records = []
        
        for record in records:
            # Create key for duplicate detection
            key = (
                record.datetime.isoformat(),
                record.value_1,
                record.value_2
            )
            
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
            else:
                record.quality_flag = QualityFlags.DUPLICATE
                unique_records.append(record)  # Keep for stats but flag as duplicate
        
        return unique_records
    
    def _apply_validation_rules(
        self, 
        records: List[HealthDataRecord], 
        metric_type: str
    ) -> List[HealthDataRecord]:
        """Apply metric-specific validation rules"""
        
        ranges = self.VALIDATION_RANGES.get(metric_type, {})
        
        for record in records:
            if record.quality_flag != QualityFlags.GOOD:
                continue  # Skip already flagged records
            
            # Check primary value
            if metric_type == 'bp':
                systolic_range = ranges.get('systolic', (0, 999))
                diastolic_range = ranges.get('diastolic', (0, 999))
                
                if not (systolic_range[0] <= record.value_1 <= systolic_range[1]):
                    record.quality_flag = QualityFlags.INVALID
                elif record.value_2 and not (diastolic_range[0] <= record.value_2 <= diastolic_range[1]):
                    record.quality_flag = QualityFlags.INVALID
                elif record.value_2 and record.value_1 <= record.value_2:
                    # Systolic should be higher than diastolic
                    record.quality_flag = QualityFlags.INVALID
                    
            elif metric_type == 'sleep':
                duration_range = ranges.get('sleep_duration', (0, 24))
                if not (duration_range[0] <= record.value_1 <= duration_range[1]):
                    record.quality_flag = QualityFlags.INVALID
                    
            elif metric_type == 'steps':
                steps_range = ranges.get('step_count', (0, 999999))
                if not (steps_range[0] <= record.value_1 <= steps_range[1]):
                    record.quality_flag = QualityFlags.INVALID
                # Steps should be non-negative
                if record.value_1 < 0:
                    record.quality_flag = QualityFlags.INVALID
                    
            elif metric_type == 'hr':
                hr_range = ranges.get('heart_rate', (30, 220))
                if not (hr_range[0] <= record.value_1 <= hr_range[1]):
                    record.quality_flag = QualityFlags.INVALID
                    
            elif metric_type == 'spo2':
                spo2_range = ranges.get('spo2', (80, 100))
                if not (spo2_range[0] <= record.value_1 <= spo2_range[1]):
                    record.quality_flag = QualityFlags.INVALID
                    
            elif metric_type == 'temp':
                temp_range = ranges.get('temperature', (90, 105))
                if not (temp_range[0] <= record.value_1 <= temp_range[1]):
                    record.quality_flag = QualityFlags.INVALID
        
        return records
    
    def _detect_outliers(
        self, 
        records: List[HealthDataRecord], 
        metric_type: str
    ) -> List[HealthDataRecord]:
        """Detect outliers using Z-score and IQR methods"""
        
        # Only consider good records for outlier detection
        good_records = [r for r in records if r.quality_flag == QualityFlags.GOOD]
        
        if len(good_records) < 5:  # Need minimum samples for outlier detection
            return records
        
        # Extract values for analysis
        values_1 = [r.value_1 for r in good_records]
        values_2 = [r.value_2 for r in good_records if r.value_2 is not None]
        
        params = self.OUTLIER_PARAMS.get(metric_type, {'z_threshold': 3.0, 'iqr_factor': 2.5})
        
        # Detect outliers in primary values
        outliers_1 = self._detect_outliers_in_series(values_1, params)
        
        # Detect outliers in secondary values if available
        outliers_2 = set()
        if values_2:
            outliers_2 = self._detect_outliers_in_series(values_2, params)
        
        # Flag outliers
        for i, record in enumerate(good_records):
            if i in outliers_1:
                record.quality_flag = QualityFlags.OUTLIER
            elif record.value_2 is not None and i in outliers_2:
                record.quality_flag = QualityFlags.OUTLIER
        
        return records
    
    def _detect_outliers_in_series(
        self, 
        values: List[float], 
        params: Dict
    ) -> Set[int]:
        """Detect outliers using both Z-score and IQR methods"""
        
        if len(values) < 5:
            return set()
        
        values_array = np.array(values)
        outliers = set()
        
        # Z-score method
        z_scores = np.abs(stats.zscore(values_array, nan_policy='omit'))
        z_outliers = np.where(z_scores > params['z_threshold'])[0]
        outliers.update(z_outliers)
        
        # IQR method
        Q1 = np.percentile(values_array, 25)
        Q3 = np.percentile(values_array, 75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - params['iqr_factor'] * IQR
        upper_bound = Q3 + params['iqr_factor'] * IQR
        
        iqr_outliers = np.where(
            (values_array < lower_bound) | (values_array > upper_bound)
        )[0]
        outliers.update(iqr_outliers)
        
        return outliers
    
    def _handle_missing_values(
        self, 
        records: List[HealthDataRecord], 
        metric_type: str
    ) -> List[HealthDataRecord]:
        """Handle missing values - currently just flags them"""
        
        for record in records:
            if record.value_1 is None or pd.isna(record.value_1):
                record.quality_flag = QualityFlags.MISSING
        
        return records
    
    def _log_cleaning_summary(self):
        """Log cleaning statistics"""
        self.logger.info("Data cleaning summary:")
        
        for metric_type, stats in self.cleaning_stats.items():
            total = stats['total_records']
            good_pct = (stats['good'] / total * 100) if total > 0 else 0
            
            self.logger.info(
                f"{metric_type}: {stats['good']}/{total} good records ({good_pct:.1f}%), "
                f"{stats['outlier']} outliers, {stats['invalid']} invalid, "
                f"{stats['duplicate']} duplicates"
            )
    
    def get_cleaning_stats(self) -> Dict:
        """Get detailed cleaning statistics"""
        return self.cleaning_stats.copy()


class DataQualityAnalyzer(BaseProcessor):
    """
    Analyzes data quality metrics for researcher reports.
    """
    
    def process(self, data: HealthDataCollection) -> Dict:
        """
        Analyze data quality across all metrics and participants.
        
        Parameters
        ----------
        data : HealthDataCollection
            Cleaned health data collection
            
        Returns
        -------
        Dict
            Quality analysis results
        """
        analysis = {
            'overall_stats': self._compute_overall_stats(data),
            'participant_stats': self._compute_participant_stats(data),
            'metric_stats': self._compute_metric_stats(data),
            'temporal_stats': self._compute_temporal_stats(data),
            'quality_flags_distribution': self._analyze_quality_flags(data),
        }
        
        return analysis
    
    def _compute_overall_stats(self, data: HealthDataCollection) -> Dict:
        """Compute overall data quality statistics"""
        
        total_records = len(data)
        if total_records == 0:
            return {}
        
        quality_counts = {}
        for record in data.records:
            flag = record.quality_flag
            quality_counts[flag] = quality_counts.get(flag, 0) + 1
        
        return {
            'total_records': total_records,
            'total_participants': len(data.get_participants()),
            'total_metrics': len(data.get_metric_types()),
            'quality_distribution': quality_counts,
            'good_data_percentage': (quality_counts.get('good', 0) / total_records) * 100,
        }
    
    def _compute_participant_stats(self, data: HealthDataCollection) -> Dict:
        """Compute per-participant quality statistics"""
        
        participant_stats = {}
        
        for participant_id in data.get_participants():
            participant_data = data.get_participant_data(participant_id)
            
            quality_counts = {}
            for record in participant_data:
                flag = record.quality_flag
                quality_counts[flag] = quality_counts.get(flag, 0) + 1
            
            total = len(participant_data)
            participant_stats[participant_id] = {
                'total_records': total,
                'quality_distribution': quality_counts,
                'good_data_percentage': (quality_counts.get('good', 0) / total) * 100 if total > 0 else 0,
                'metrics_available': len(set(r.metric_type for r in participant_data)),
            }
        
        return participant_stats
    
    def _compute_metric_stats(self, data: HealthDataCollection) -> Dict:
        """Compute per-metric quality statistics"""
        
        metric_stats = {}
        
        for metric_type in data.get_metric_types():
            metric_data = data.get_metric_data(metric_type)
            
            quality_counts = {}
            for record in metric_data:
                flag = record.quality_flag
                quality_counts[flag] = quality_counts.get(flag, 0) + 1
            
            total = len(metric_data)
            metric_stats[metric_type] = {
                'total_records': total,
                'quality_distribution': quality_counts,
                'good_data_percentage': (quality_counts.get('good', 0) / total) * 100 if total > 0 else 0,
                'participants_with_data': len(set(r.participant_id for r in metric_data)),
            }
        
        return metric_stats
    
    def _compute_temporal_stats(self, data: HealthDataCollection) -> Dict:
        """Compute temporal data quality statistics"""
        
        if not data.records:
            return {}
        
        # Get date range
        dates = [r.datetime.date() for r in data.records]
        min_date = min(dates)
        max_date = max(dates)
        
        # Compute daily stats
        daily_stats = {}
        for record in data.records:
            date_str = record.datetime.date().isoformat()
            if date_str not in daily_stats:
                daily_stats[date_str] = {'total': 0, 'good': 0}
            
            daily_stats[date_str]['total'] += 1
            if record.quality_flag == 'good':
                daily_stats[date_str]['good'] += 1
        
        return {
            'date_range': {
                'start': min_date.isoformat(),
                'end': max_date.isoformat(),
                'days': (max_date - min_date).days + 1,
            },
            'daily_stats': daily_stats,
        }
    
    def _analyze_quality_flags(self, data: HealthDataCollection) -> Dict:
        """Analyze distribution of quality flags"""
        
        flag_analysis = {}
        
        for metric_type in data.get_metric_types():
            metric_data = data.get_metric_data(metric_type)
            
            flag_counts = {}
            for record in metric_data:
                flag = record.quality_flag
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
            
            flag_analysis[metric_type] = flag_counts
        
        return flag_analysis


def clean_goqii_data(data: HealthDataCollection) -> Tuple[HealthDataCollection, Dict]:
    """
    Convenience function to clean GOQII health data.
    
    Parameters
    ----------
    data : HealthDataCollection
        Raw health data collection
        
    Returns
    -------
    Tuple[HealthDataCollection, Dict]
        (cleaned_data_collection, quality_analysis)
    """
    # Clean data
    cleaner = HealthDataCleaner()
    cleaned_data = cleaner.process(data)
    
    # Analyze quality
    analyzer = DataQualityAnalyzer()
    quality_analysis = analyzer.process(cleaned_data)
    
    return cleaned_data, quality_analysis


if __name__ == "__main__":
    # Example usage with sample data
    from .data_loader import load_goqii_data
    import sys
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = "./input"
    
    print(f"Loading and cleaning GOQII data from: {input_path}")
    
    try:
        # Load data
        raw_data, loading_summary = load_goqii_data(input_path)
        print(f"Loaded {len(raw_data)} raw records")
        
        # Clean data
        cleaned_data, quality_analysis = clean_goqii_data(raw_data)
        print(f"Cleaned data: {len(cleaned_data)} records")
        
        # Display quality summary
        overall = quality_analysis['overall_stats']
        print(f"Good data percentage: {overall['good_data_percentage']:.1f}%")
        
        print("\nQuality by metric:")
        for metric, stats in quality_analysis['metric_stats'].items():
            print(f"  {metric}: {stats['good_data_percentage']:.1f}% good data")
            
    except Exception as e:
        print(f"Error processing data: {e}")
        sys.exit(1)
