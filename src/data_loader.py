"""
Data loading and standardization module for GOQII Health Data EDA Protocol

Handles discovery of participant folders, loading CSV/JSON files,
and converting to standardized HealthDataRecord format.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings
import logging

from .core import (
    HealthDataRecord, 
    HealthDataCollection, 
    standardize_participant_data,
    BaseProcessor
)


class DataDiscovery:
    """
    Discovers and catalogs participant data files in the input directory.
    """
    
    EXPECTED_PATTERNS = {
        'bp': 'bp_*.csv',
        'sleep': 'sleep_*.csv', 
        'steps': 'steps_*.csv',
        'hr': 'heartrate_*.json',
        'spo2': 'spo2_*.json',
        'temp': 'temperature_*.json'
    }
    
    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Add paths to meals and lungs data directories
        self.meals_dir = self.input_dir / 'meals_data'
        self.lungs_dir = self.input_dir / 'lungs_data'
    
    def discover_participants(self) -> Dict[str, Dict[str, List[Path]]]:
        """
        Scan input directory for participant folders and their data files.
        Also checks the physio_data directory directly for files.
        
        Returns
        -------
        Dict[str, Dict[str, List[Path]]]
            Nested dict: {participant_id: {metric_type: [file_paths]}}
        """
        participants = {}
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
        
        # First, check for direct physio_data folder
        physio_dir = self.input_dir / 'physio_data'
        if physio_dir.exists() and physio_dir.is_dir():
            self.logger.info(f"Found physio_data directory: {physio_dir}")
            
            # Create a default participant for files in physio_data
            participant_id = 'participant-default'
            participant_files = {}
            
            # Check for expected file patterns in physio_data directory
            for metric_type, pattern in self.EXPECTED_PATTERNS.items():
                files = list(physio_dir.glob(pattern))
                if files:
                    participant_files[metric_type] = files
                    self.logger.info(f"Found {len(files)} {metric_type} files in physio_data directory")
            
            if participant_files:  # Add if we found any files
                participants[participant_id] = participant_files
                total_files = sum(len(files) for files in participant_files.values())
                self.logger.info(f"Added default participant with {total_files} data files from physio_data")
        
        # Then, look for participant folders (both participant-* and Participant_*)
        for participant_folder in self.input_dir.glob('*articipant*'):
            if not participant_folder.is_dir():
                continue
                
            participant_id = participant_folder.name
            # Normalize participant ID
            if not participant_id.startswith('participant-'):
                if participant_id.lower().startswith('participant'):
                    participant_id = 'participant-' + participant_id.split('_')[-1]
            
            participant_files = {}
            
            # Check for expected file patterns
            for metric_type, pattern in self.EXPECTED_PATTERNS.items():
                files = list(participant_folder.glob(pattern))
                if files:
                    participant_files[metric_type] = files
                    self.logger.info(f"Found {len(files)} {metric_type} files for {participant_id}")
            
            if participant_files:  # Only include participants with at least one file
                participants[participant_id] = participant_files
                total_files = sum(len(files) for files in participant_files.values())
                self.logger.info(f"Found {participant_id} with {total_files} data files")
        
        self.logger.info(f"Discovered {len(participants)} participants")
        return participants
    
    def get_participant_summary(self, participants: Dict[str, Dict[str, List[Path]]]) -> pd.DataFrame:
        """
        Create summary DataFrame of discovered participants and their data files.
        """
        summary_data = []
        
        for participant_id, files in participants.items():
            row = {'participant_id': participant_id}
            
            # Add file availability and counts
            total_files = 0
            for metric_type in self.EXPECTED_PATTERNS.keys():
                has_files = metric_type in files
                row[f'has_{metric_type}'] = has_files
                if has_files:
                    count = len(files[metric_type])
                    row[f'{metric_type}_count'] = count
                    total_files += count
                else:
                    row[f'{metric_type}_count'] = 0
            
            # Add file count
            row['total_files'] = total_files
            
            summary_data.append(row)
        
        return pd.DataFrame(summary_data)


class FileLoader:
    """
    Loads CSV and JSON files and converts them to pandas DataFrames.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Load CSV file with error handling and basic validation.
        """
        try:
            df = pd.read_csv(file_path)
            self.logger.debug(f"Loaded CSV: {file_path} ({len(df)} rows)")
            return df
        except Exception as e:
            self.logger.error(f"Failed to load CSV {file_path}: {e}")
            return pd.DataFrame()
    
    def load_json(self, file_path: Path) -> pd.DataFrame:
        """
        Load JSON file and flatten to DataFrame.
        
        Handles both:
        - Array of objects: [{"timestamp": "...", "value": 123}, ...]
        - Single object with arrays: {"timestamps": [...], "values": [...]}
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # Array of objects
                df = pd.json_normalize(data)
            elif isinstance(data, dict):
                # Try to create DataFrame from dict
                df = pd.DataFrame(data)
            else:
                self.logger.warning(f"Unexpected JSON structure in {file_path}")
                return pd.DataFrame()
            
            self.logger.debug(f"Loaded JSON: {file_path} ({len(df)} rows)")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load JSON {file_path}: {e}")
            return pd.DataFrame()
    
    def load_file(self, file_path: Path) -> pd.DataFrame:
        """
        Load file based on extension (.csv or .json).
        """
        if file_path.suffix.lower() == '.csv':
            return self.load_csv(file_path)
        elif file_path.suffix.lower() == '.json':
            return self.load_json(file_path)
        else:
            self.logger.error(f"Unsupported file format: {file_path}")
            return pd.DataFrame()


class DataStandardizer(BaseProcessor):
    """
    Converts raw DataFrames to standardized HealthDataRecord format.
    """
    
    # Column mapping for GOQII data sources
    COLUMN_MAPPINGS = {
        'bp': {
            'datetime_cols': ['createdTime', 'logDate', 'logDateTime'],
            'value_cols': ['systolic'],
            'secondary_cols': ['diastolic'],
            'quality_cols': ['status']
        },
        'sleep': {
            'datetime_cols': ['logDateTime', 'logDate', 'createdTime'],
            'value_cols': ['lightSleep', 'deepSleep', 'almostAwake'],  # Will sum these
            'secondary_cols': [],
            'quality_cols': ['status']
        },
        'steps': {
            'datetime_cols': ['logDateTime', 'logDate', 'createdTime'],
            'value_cols': ['steps'],
            'secondary_cols': ['distance', 'calories'],
            'quality_cols': ['status']
        },
        'hr': {
            'datetime_cols': ['logDateTime', 'group', 'createdTime'],
            'value_cols': ['averageSessionHeartRate', 'lastRate', 'heartRate'],
            'secondary_cols': ['maxRate', 'minRate'],
            'quality_cols': []
        },
        'spo2': {
            'datetime_cols': ['createdTime', 'logDate', 'timestamp'],
            'value_cols': ['spo2', 'oxygen_saturation', 'value'],
            'secondary_cols': ['confidence', 'quality'],
            'quality_cols': []
        },
        'temp': {
            'datetime_cols': ['createdTime', 'logDate', 'timestamp'],
            'value_cols': ['temperature', 'temp', 'value'],
            'secondary_cols': ['ambient_temp'],
            'quality_cols': []
        }
    }
    
    def process(self, data: Tuple[pd.DataFrame, str, str]) -> List[HealthDataRecord]:
        """
        Process raw DataFrame to standardized HealthDataRecord format.
        
        Parameters
        ----------
        data : Tuple[pd.DataFrame, str, str]
            (dataframe, participant_id, metric_type)
        
        Returns
        -------
        List[HealthDataRecord]
            Standardized health records
        """
        df, participant_id, metric_type = data
        
        if df.empty:
            return []
        
        try:
            # Handle JSON data differently
            if isinstance(df.iloc[0, 0] if len(df) > 0 else None, (list, dict)):
                df = self._flatten_json_data(df, metric_type)
            
            # Apply GOQII-specific column mapping
            df_standardized = self._apply_goqii_mapping(df, metric_type)
            
            # Convert to HealthDataRecord format
            records = self._create_health_records(df_standardized, participant_id, metric_type)
            
            self.logger.info(f"Standardized {len(records)} records for {participant_id}/{metric_type}")
            return records
            
        except Exception as e:
            self.logger.error(f"Error standardizing {participant_id}/{metric_type}: {str(e)}")
            return []
    
    def _flatten_json_data(self, df: pd.DataFrame, metric_type: str) -> pd.DataFrame:
        """Handle nested JSON structures in DataFrames"""
        
        try:
            if metric_type == 'hr':
                # Heart rate JSON has nested jsonData array
                flattened_rows = []
                
                for _, row in df.iterrows():
                    if 'jsonData' in row and isinstance(row['jsonData'], list):
                        for json_item in row['jsonData']:
                            flat_row = {}
                            # Copy top-level data
                            for key, value in row.items():
                                if key != 'jsonData':
                                    flat_row[key] = value
                            # Add nested data
                            if isinstance(json_item, dict):
                                flat_row.update(json_item)
                            flattened_rows.append(flat_row)
                    else:
                        flattened_rows.append(dict(row))
                
                return pd.DataFrame(flattened_rows)
            
            else:
                # For other JSON files, try direct normalization
                if len(df) > 0 and isinstance(df.iloc[0, 0], (list, dict)):
                    # If first column contains JSON, normalize it
                    first_col_data = df.iloc[0, 0]
                    if isinstance(first_col_data, list):
                        return pd.json_normalize(first_col_data)
                    elif isinstance(first_col_data, dict):
                        return pd.json_normalize([first_col_data])
                
                return df
                
        except Exception as e:
            self.logger.warning(f"Could not flatten JSON for {metric_type}: {str(e)}")
            return df
    
    def _apply_goqii_mapping(self, df: pd.DataFrame, metric_type: str) -> pd.DataFrame:
        """Apply GOQII-specific column mapping"""
        
        if metric_type not in self.COLUMN_MAPPINGS:
            self.logger.warning(f"No mapping defined for metric type: {metric_type}")
            return df
        
        mapping = self.COLUMN_MAPPINGS[metric_type]
        standardized = pd.DataFrame()
        
        # Find datetime column
        datetime_col = None
        for col_name in mapping['datetime_cols']:
            if col_name in df.columns:
                datetime_col = col_name
                break
        
        if not datetime_col:
            self.logger.error(f"No datetime column found for {metric_type}")
            return pd.DataFrame()
        
        standardized['datetime'] = df[datetime_col]
        
        # Find value column
        value_col = None
        for col_name in mapping['value_cols']:
            if col_name in df.columns:
                value_col = col_name
                break
        
        if not value_col:
            self.logger.error(f"No value column found for {metric_type}")
            return pd.DataFrame()
        
        # Special handling for sleep (sum multiple columns)
        if metric_type == 'sleep' and all(col in df.columns for col in ['lightSleep', 'deepSleep']):
            standardized['value_1'] = df['lightSleep'].fillna(0) + df['deepSleep'].fillna(0) + df['almostAwake'].fillna(0)
        else:
            standardized['value_1'] = df[value_col]
        
        # Find secondary value column
        secondary_col = None
        if mapping['secondary_cols']:
            for col_name in mapping['secondary_cols']:
                if col_name in df.columns:
                    secondary_col = col_name
                    break
        
        if secondary_col:
            standardized['value_2'] = df[secondary_col]
        else:
            standardized['value_2'] = None
        
        return standardized
    
    def _create_health_records(self, df: pd.DataFrame, participant_id: str, metric_type: str) -> List[HealthDataRecord]:
        """Create HealthDataRecord objects from standardized DataFrame"""
        
        records = []
        
        for _, row in df.iterrows():
            try:
                # Parse datetime
                datetime_val = pd.to_datetime(row['datetime'], errors='coerce')
                if pd.isna(datetime_val):
                    continue
                
                # Parse values
                value_1 = pd.to_numeric(row['value_1'], errors='coerce')
                value_2 = pd.to_numeric(row['value_2'], errors='coerce') if row.get('value_2') is not None else None
                
                if pd.isna(value_1):
                    continue
                
                record = HealthDataRecord(
                    participant_id=participant_id,
                    metric_type=metric_type,
                    datetime=datetime_val,
                    value_1=float(value_1),
                    value_2=float(value_2) if value_2 is not None and not pd.isna(value_2) else None,
                    quality_flag='good'  # Will be updated by data cleaner
                )
                
                records.append(record)
                
            except Exception as e:
                self.logger.debug(f"Skipped row due to parsing error: {str(e)}")
                continue
        
        return records
    
    def _apply_column_mapping(self, df: pd.DataFrame, metric_type: str) -> pd.DataFrame:
        """
        Apply column name mapping to standardize column names.
        """
        df_mapped = df.copy()
        
        mappings = self.COLUMN_MAPPINGS.get(metric_type, {}).get('common_mappings', [])
        
        for possible_names, standard_name in mappings:
            # Find first matching column
            for possible_name in possible_names:
                if possible_name in df_mapped.columns:
                    if standard_name != possible_name:  # Only rename if different
                        df_mapped = df_mapped.rename(columns={possible_name: standard_name})
                    break
        
        return df_mapped


class DataLoader(BaseProcessor):
    """
    Main data loading pipeline that orchestrates discovery, loading, and standardization.
    """
    
    def __init__(self, input_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.input_dir = input_dir
        self.discovery = DataDiscovery(input_dir)
        self.file_loader = FileLoader()
        self.standardizer = DataStandardizer()
        self.meals_data = None
        self.lungs_data = None
    
    def process(self, data=None) -> HealthDataCollection:
        """
        Main processing pipeline: discover -> load -> standardize.
        
        Returns
        -------
        HealthDataCollection
            Collection of all loaded and standardized health data
        """
        # Phase 1: Discover participant files
        self.logger.info("Phase 1: Discovering participant data files")
        participants = self.discovery.discover_participants()
        
        # Load meals data
        self.logger.info("Loading meals data")
        self.meals_data = self._load_meals_data()
        
        # Load lungs data
        self.logger.info("Loading lungs data")
        self.lungs_data = self._load_lungs_data()
        
        if not participants:
            self.logger.warning("No participants found!")
            return HealthDataCollection()
        
        # Phase 2: Load and standardize data
        self.logger.info("Phase 2: Loading and standardizing data")
        collection = HealthDataCollection()
        
        for participant_id, files_by_metric in participants.items():
            self.logger.info(f"Processing participant: {participant_id}")
            
            for metric_type, file_list in files_by_metric.items():
                # Process multiple files for this metric
                all_records = []
                
                for file_path in file_list:
                    self.logger.debug(f"Loading {file_path}")
                    # Load raw data
                    df = self.file_loader.load_file(file_path)
                    if df.empty:
                        continue
                    
                    # Standardize data
                    records = self.standardizer.process((df, participant_id, metric_type))
                    if records:
                        all_records.extend(records)
                
                if all_records:
                    self.logger.info(f"Loaded {len(all_records)} {metric_type} records for {participant_id}")
                    collection.add_records(all_records)
        
        self.logger.info(f"Data loading complete: {len(collection)} total records")
        return collection
    
    def get_loading_summary(self) -> Dict:
        """
        Get summary of data loading process.
        """
        participants = self.discovery.discover_participants()
        summary_df = self.discovery.get_participant_summary(participants)
        
        # Add meals and lungs data summary
        meals_info = {}
        if self.meals_data is not None and not self.meals_data.empty:
            meals_info = {
                'record_count': len(self.meals_data),
                'unique_dishes': len(self.meals_data['dish'].unique()) if 'dish' in self.meals_data.columns else 0,
                'date_range': {
                    'start': self.meals_data['date'].min().strftime('%Y-%m-%d') if 'date' in self.meals_data.columns and not self.meals_data.empty else 'Unknown',
                    'end': self.meals_data['date'].max().strftime('%Y-%m-%d') if 'date' in self.meals_data.columns and not self.meals_data.empty else 'Unknown'
                }
            }
        
        lungs_info = {}
        if self.lungs_data is not None and not self.lungs_data.empty:
            lungs_info = {
                'record_count': len(self.lungs_data),
                'metrics': list(self.lungs_data.columns[3:]) if len(self.lungs_data.columns) > 3 else []
            }
        
        return {
            'total_participants': len(participants),
            'participants_by_file_count': summary_df['total_files'].value_counts().to_dict() if not summary_df.empty else {},
            'metric_availability': {
                metric: summary_df[f'has_{metric}'].sum() if not summary_df.empty else 0
                for metric in DataDiscovery.EXPECTED_PATTERNS.keys()
            },
            'discovery_summary': summary_df.to_dict('records') if not summary_df.empty else [],
            'date_range': self._get_date_range(participants),
            'meals_data': meals_info,
            'lungs_data': lungs_info
        }
    
    def _get_date_range(self, participants: Dict) -> Dict:
        """Extract date range from participant data"""
        dates = []
        
        for participant_files in participants.values():
            for file_list in participant_files.values():
                for file_path in file_list:
                    # Extract date from filename timestamp
                    try:
                        timestamp = int(file_path.stem.split('_')[-1])
                        from datetime import datetime
                        date = datetime.fromtimestamp(timestamp)
                        dates.append(date)
                    except (ValueError, IndexError):
                        continue
        
        if dates:
            return {
                'start': min(dates).strftime('%Y-%m-%d'),
                'end': max(dates).strftime('%Y-%m-%d'),
                'span_days': (max(dates) - min(dates)).days
            }
        else:
            return {'start': 'Unknown', 'end': 'Unknown', 'span_days': 0}
            
    def _load_meals_data(self) -> pd.DataFrame:
        """Load meals data from CSV file."""
        try:
            meals_path = self.discovery.meals_dir / "Combined Meals Data.csv"
            if not meals_path.exists():
                self.logger.warning("Meals data file not found")
                return pd.DataFrame()
                
            self.logger.info(f"Loading meals data from: {meals_path}")
            meals_df = self.file_loader.load_csv(meals_path)
            
            if not meals_df.empty:
                # Convert time column to datetime (timestamp in milliseconds)
                if 'time' in meals_df.columns:
                    try:
                        meals_df['date'] = pd.to_datetime(meals_df['time'], unit='ms')
                        meals_df['date'] = meals_df['date'].dt.date
                    except Exception as e:
                        self.logger.error(f"Error converting meal times to dates: {str(e)}")
                
                self.logger.info(f"Meals data loaded successfully with {len(meals_df)} records")
            return meals_df
            
        except Exception as e:
            self.logger.error(f"Error loading meals data: {str(e)}")
            return pd.DataFrame()
    
    def _load_lungs_data(self) -> pd.DataFrame:
        """Load lungs data from CSV file."""
        try:
            lungs_path = self.discovery.lungs_dir / "spirometry.csv"
            if not lungs_path.exists():
                self.logger.warning("Lungs data file not found")
                return pd.DataFrame()
                
            self.logger.info(f"Loading lungs data from: {lungs_path}")
            lungs_df = self.file_loader.load_csv(lungs_path)
            
            if not lungs_df.empty:
                self.logger.info(f"Lungs data loaded successfully with {len(lungs_df)} records")
            return lungs_df
            
        except Exception as e:
            self.logger.error(f"Error loading lungs data: {str(e)}")
            return pd.DataFrame()


def load_goqii_data(input_dir: str) -> Tuple[HealthDataCollection, Dict, pd.DataFrame, pd.DataFrame]:
    """
    Convenience function to load GOQII health data.
    
    Parameters
    ----------
    input_dir : str
        Path to input directory containing participant-* folders
    
    Returns
    -------
    Tuple[HealthDataCollection, Dict, pd.DataFrame, pd.DataFrame]
        (data_collection, loading_summary, meals_data, lungs_data)
    """
    loader = DataLoader(input_dir)
    
    # Load data
    collection = loader.process()
    
    # Get summary
    summary = loader.get_loading_summary()
    
    # Return with additional data
    return collection, summary, loader.meals_data, loader.lungs_data


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = "./input"
    
    print(f"Loading GOQII data from: {input_path}")
    
    try:
        collection, summary = load_goqii_data(input_path)
        
        print(f"\nLoading Summary:")
        print(f"Total participants: {summary['total_participants']}")
        print(f"Total records: {len(collection)}")
        print(f"Participants: {collection.get_participants()}")
        print(f"Metrics: {collection.get_metric_types()}")
        
        # Display metric availability
        print(f"\nMetric Availability:")
        for metric, count in summary['metric_availability'].items():
            print(f"  {metric}: {count} participants")
            
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
