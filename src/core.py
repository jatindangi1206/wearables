"""
Core data structures and base classes for GOQII Health Data EDA Protocol

Inspired by scikit-digital-health's design patterns but adapted for multi-modal
wearable health data (BP, sleep, steps, HR, SpO2, temperature).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import warnings


@dataclass
class HealthDataRecord:
    """
    Unified data record structure for all health metrics.
    Follows scikit-digital-health patterns but extended for GOQII data.
    """
    participant_id: str
    metric_type: str  # 'bp', 'sleep', 'steps', 'hr', 'spo2', 'temp'
    datetime: pd.Timestamp
    value_1: float  # Primary value (systolic BP, sleep hours, step count, HR, SpO2, temp)
    value_2: Optional[float] = None  # Secondary value (diastolic BP, sleep quality score, etc.)
    unit: str = ""
    metadata: Optional[Dict[str, Any]] = None
    quality_flag: str = "good"  # 'good', 'outlier', 'missing', 'invalid'
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseProcessor(ABC):
    """
    Abstract base class for all data processors.
    Follows scikit-digital-health BaseProcess pattern.
    """
    
    def __init__(self, **kwargs):
        self.params = kwargs
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        import logging
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Main processing method to be implemented by subclasses"""
        pass
    
    def validate_input(self, data: Any) -> bool:
        """Validate input data format"""
        return True
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.params})"


class HealthDataSchema:
    """
    Schema definitions for different health metrics.
    Defines expected columns, data types, and validation rules.
    """
    
    SCHEMAS = {
        'bp': {
            'required_columns': ['datetime', 'systolic', 'diastolic'],
            'optional_columns': ['pulse', 'device_id'],
            'value_1_col': 'systolic',
            'value_2_col': 'diastolic',
            'unit': 'mmHg',
            'valid_range_1': (80, 200),
            'valid_range_2': (50, 130),
        },
        'sleep': {
            'required_columns': ['datetime', 'sleep_duration'],
            'optional_columns': ['sleep_quality', 'deep_sleep', 'light_sleep', 'rem_sleep'],
            'value_1_col': 'sleep_duration',
            'value_2_col': 'sleep_quality',
            'unit': 'hours',
            'valid_range_1': (0, 24),
            'valid_range_2': (0, 100),  # quality score 0-100
        },
        'steps': {
            'required_columns': ['datetime', 'step_count'],
            'optional_columns': ['distance', 'calories'],
            'value_1_col': 'step_count',
            'value_2_col': 'distance',
            'unit': 'steps',
            'valid_range_1': (0, 50000),
            'valid_range_2': (0, 100),  # km
        },
        'hr': {
            'required_columns': ['datetime', 'heart_rate'],
            'optional_columns': ['resting_hr', 'max_hr'],
            'value_1_col': 'heart_rate',
            'value_2_col': 'resting_hr',
            'unit': 'bpm',
            'valid_range_1': (30, 220),
            'valid_range_2': (30, 120),
        },
        'spo2': {
            'required_columns': ['datetime', 'spo2'],
            'optional_columns': ['confidence'],
            'value_1_col': 'spo2',
            'value_2_col': 'confidence',
            'unit': '%',
            'valid_range_1': (80, 100),
            'valid_range_2': (0, 100),
        },
        'temp': {
            'required_columns': ['datetime', 'temperature'],
            'optional_columns': ['ambient_temp'],
            'value_1_col': 'temperature',
            'value_2_col': 'ambient_temp',
            'unit': '°F',
            'valid_range_1': (90, 105),
            'valid_range_2': (50, 120),
        }
    }
    
    @classmethod
    def get_schema(cls, metric_type: str) -> Dict:
        """Get schema for a specific metric type"""
        return cls.SCHEMAS.get(metric_type, {})
    
    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame, metric_type: str) -> Tuple[bool, List[str]]:
        """Validate DataFrame against schema"""
        schema = cls.get_schema(metric_type)
        if not schema:
            return False, [f"Unknown metric type: {metric_type}"]
        
        errors = []
        
        # Check required columns
        missing_cols = set(schema['required_columns']) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check datetime column
        if 'datetime' in df.columns:
            try:
                pd.to_datetime(df['datetime'])
            except Exception as e:
                errors.append(f"Invalid datetime format: {e}")
        
        return len(errors) == 0, errors


def ensure_timezone_aware(dt: Union[pd.Timestamp, datetime], tz: str = 'UTC') -> pd.Timestamp:
    """
    Ensure datetime is timezone-aware (UTC by default).
    Follows scikit-digital-health timestamp handling patterns.
    """
    if isinstance(dt, datetime):
        dt = pd.Timestamp(dt)
    
    if dt.tz is None:
        dt = dt.tz_localize(tz)
    elif dt.tz != timezone.utc and tz == 'UTC':
        dt = dt.tz_convert('UTC')
    
    return dt


def standardize_participant_data(
    df: pd.DataFrame,
    participant_id: str,
    metric_type: str,
    timezone: str = 'UTC'
) -> List[HealthDataRecord]:
    """
    Convert raw DataFrame to standardized HealthDataRecord format.
    
    Parameters
    ----------
    df : pd.DataFrame
        Raw data from CSV/JSON
    participant_id : str
        Participant identifier
    metric_type : str
        Type of health metric
    timezone : str
        Timezone for datetime conversion
    
    Returns
    -------
    List[HealthDataRecord]
        Standardized health records
    """
    schema = HealthDataSchema.get_schema(metric_type)
    if not schema:
        raise ValueError(f"Unknown metric type: {metric_type}")
    
    # Validate input
    is_valid, errors = HealthDataSchema.validate_dataframe(df, metric_type)
    if not is_valid:
        warnings.warn(f"Schema validation failed for {participant_id}/{metric_type}: {errors}")
    
    records = []
    
    for _, row in df.iterrows():
        try:
            # Convert datetime
            dt = ensure_timezone_aware(pd.to_datetime(row['datetime']), timezone)
            
            # Extract primary and secondary values  
            try:
                value_1 = float(row[schema['value_1_col']])  # type: ignore
            except (ValueError, TypeError, KeyError):
                continue  # Skip rows with invalid primary values
            
            value_2 = None
            if schema.get('value_2_col') and schema['value_2_col'] in df.columns:
                try:
                    value_2_raw = row[schema['value_2_col']]  # type: ignore
                    if not pd.isna(value_2_raw):
                        value_2 = float(value_2_raw)  # type: ignore
                except (ValueError, TypeError, KeyError):
                    value_2 = None
            
            # Create metadata from optional columns
            metadata = {}
            for col in df.columns:
                if col not in ['datetime', schema['value_1_col'], schema.get('value_2_col')]:
                    metadata[col] = row[col]
            
            # Create record
            record = HealthDataRecord(
                participant_id=participant_id,
                metric_type=metric_type,
                datetime=dt,
                value_1=value_1,
                value_2=value_2,
                unit=schema['unit'],
                metadata=metadata,
                quality_flag='good'  # Will be updated by cleaning process
            )
            
            records.append(record)
            
        except Exception as e:
            # Skip invalid rows but log the error
            warnings.warn(f"Skipped invalid row for {participant_id}/{metric_type}: {e}")
            continue
    
    return records


def convert_to_dataframe(records: List[HealthDataRecord]) -> pd.DataFrame:
    """
    Convert list of HealthDataRecord back to pandas DataFrame.
    Useful for analysis and reporting.
    """
    if not records:
        return pd.DataFrame()
    
    data = []
    for record in records:
        row = {
            'participant_id': record.participant_id,
            'metric_type': record.metric_type,
            'datetime': record.datetime,
            'value_1': record.value_1,
            'value_2': record.value_2,
            'unit': record.unit,
            'quality_flag': record.quality_flag,
        }
        
        # Add metadata as separate columns
        if record.metadata:
            row.update(record.metadata)
        
        data.append(row)
    
    return pd.DataFrame(data)


class HealthDataCollection:
    """
    Container for managing multiple participants' health data.
    Provides easy access and filtering capabilities.
    """
    
    def __init__(self):
        self.records: List[HealthDataRecord] = []
        self._index_cache = {}
    
    def add_records(self, records: List[HealthDataRecord]):
        """Add new records to the collection"""
        self.records.extend(records)
        self._clear_cache()
    
    def get_participant_data(self, participant_id: str) -> List[HealthDataRecord]:
        """Get all data for a specific participant"""
        return [r for r in self.records if r.participant_id == participant_id]
    
    def get_metric_data(self, metric_type: str) -> List[HealthDataRecord]:
        """Get all data for a specific metric type"""
        return [r for r in self.records if r.metric_type == metric_type]
    
    def get_participant_metric_data(
        self, 
        participant_id: str, 
        metric_type: str
    ) -> List[HealthDataRecord]:
        """Get data for specific participant and metric"""
        return [r for r in self.records 
                if r.participant_id == participant_id and r.metric_type == metric_type]
    
    def get_participants(self) -> List[str]:
        """Get list of all participant IDs"""
        return list(set(r.participant_id for r in self.records))
    
    def get_metric_types(self) -> List[str]:
        """Get list of all metric types"""
        return list(set(r.metric_type for r in self.records))
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert entire collection to DataFrame"""
        return convert_to_dataframe(self.records)
    
    def filter_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> 'HealthDataCollection':
        """Filter records by date range"""
        filtered_records = [
            r for r in self.records 
            if start_date <= r.datetime <= end_date
        ]
        
        new_collection = HealthDataCollection()
        new_collection.add_records(filtered_records)
        return new_collection
    
    def filter_by_quality(self, quality_flags: List[str]) -> 'HealthDataCollection':
        """Filter records by quality flags"""
        filtered_records = [
            r for r in self.records 
            if r.quality_flag in quality_flags
        ]
        
        new_collection = HealthDataCollection()
        new_collection.add_records(filtered_records)
        return new_collection
    
    def _clear_cache(self):
        """Clear internal caches when data changes"""
        self._index_cache.clear()
    
    def __len__(self):
        return len(self.records)
    
    def __repr__(self):
        n_participants = len(self.get_participants())
        n_metrics = len(self.get_metric_types())
        return f"HealthDataCollection({len(self.records)} records, {n_participants} participants, {n_metrics} metrics)"
