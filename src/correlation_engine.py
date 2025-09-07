"""
Correlation analysis engine for GOQII Health Data EDA Protocol

Provides comprehensive correlation analysis between all health metrics:
- Pairwise correlations (Pearson + Spearman)
- Daily comparisons (lag-1 effects)
- 14-day rolling window analysis
- Anomaly detection and recovery patterns
- Deviation analysis for meal correlations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta, date
import json
from pathlib import Path
from scipy.stats import pearsonr, spearmanr
from sklearn.preprocessing import StandardScaler
import warnings
import logging

from .core import HealthDataRecord, HealthDataCollection, BaseProcessor


class CorrelationEngine(BaseProcessor):
    """
    Main correlation analysis engine for individual participants.
    """
    
    # All possible metric pairs for correlation analysis
    CORRELATION_PAIRS = [
        ('steps', 'sleep'),
        ('steps', 'hr'),
        ('steps', 'bp'),
        ('steps', 'temp'),
        ('steps', 'spo2'),
        ('sleep', 'hr'),
        ('sleep', 'temp'),
        ('sleep', 'spo2'),
        ('sleep', 'bp'),
        ('hr', 'temp'),
        ('hr', 'bp'),
        ('hr', 'spo2'),
        ('temp', 'spo2'),
        ('temp', 'bp'),
        ('spo2', 'bp'),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_days = kwargs.get('min_days', 7)  # Minimum days for correlation
        
    def analyze_deviations(self, cleaned_data, processed_meals=None):
        """
        Analyze deviations in physiological metrics and correlate with meals data if available.
        
        Args:
            cleaned_data: Cleaned physiological data
            processed_meals: Processed meals data (optional)
            
        Returns:
            Dictionary with deviation analysis results
        """
        self.logger.info("Analyzing deviations in physiological metrics")
        
        # Initialize results
        deviations = {
            'metrics': {},
            'significant_changes': [],
            'meal_correlations': []
        }
        
        try:
            # If no data is available, return empty analysis
            if cleaned_data is None:
                self.logger.warning("No good quality records for deviation analysis")
                return deviations
                
            # Check if it's a DataFrame or a HealthDataCollection
            if hasattr(cleaned_data, 'empty') and cleaned_data.empty:
                self.logger.warning("Empty DataFrame provided for deviation analysis")
                return deviations
                
            if hasattr(cleaned_data, 'records') and len(cleaned_data.records) == 0:
                self.logger.warning("Empty HealthDataCollection provided for deviation analysis")
                return deviations
                
            # Extract daily averages for key metrics
            daily_metrics = {}
            key_metrics = ['steps', 'sleep_duration', 'resting_hr', 'systolic', 'diastolic', 'spo2', 'temperature']
            
            # Handle DataFrame vs HealthDataCollection
            if hasattr(cleaned_data, 'columns'):
                # It's a DataFrame
                for metric in key_metrics:
                    if metric in cleaned_data.columns:
                        daily_metrics[metric] = cleaned_data.groupby('date')[metric].mean().reset_index()
            elif hasattr(cleaned_data, 'records'):
                # It's a HealthDataCollection - convert to DataFrame first
                try:
                    # Convert to a DataFrame for analysis
                    records_data = []
                    for record in cleaned_data.records:
                        # Extract date from timestamp
                        date_value = record.datetime.date() if hasattr(record.datetime, 'date') else record.datetime.to_pydatetime().date()
                        
                        # Map metric types to values
                        metric_map = {
                            'steps': ('steps', record.value_1 if record.metric_type == 'steps' else None),
                            'sleep': ('sleep_duration', record.value_1 if record.metric_type == 'sleep' else None),
                            'hr': ('resting_hr', record.value_1 if record.metric_type == 'hr' else None),
                            'bp': ('systolic', record.value_1 if record.metric_type == 'bp' else None, 
                                   'diastolic', record.value_2 if record.metric_type == 'bp' else None),
                            'temp': ('temperature', record.value_1 if record.metric_type == 'temp' else None),
                            'spo2': ('spo2', record.value_1 if record.metric_type == 'spo2' else None)
                        }
                        
                        if record.metric_type in metric_map:
                            if record.metric_type == 'bp':
                                records_data.append({
                                    'date': date_value,
                                    'systolic': record.value_1,
                                    'diastolic': record.value_2
                                })
                            else:
                                metric_name, value = metric_map[record.metric_type]
                                if value is not None:
                                    records_data.append({
                                        'date': date_value,
                                        metric_name: value
                                    })
                    
                    if records_data:
                        df = pd.DataFrame(records_data)
                        for metric in key_metrics:
                            if metric in df.columns:
                                daily_metrics[metric] = df.groupby('date')[metric].mean().reset_index()
                except Exception as e:
                    self.logger.error(f"Error converting HealthDataCollection to DataFrame: {str(e)}")
                    # Return empty analysis
                    return deviations
            
            # Calculate deviations for each metric
            for metric_name, metric_data in daily_metrics.items():
                if len(metric_data) < 3:  # Need at least 3 days for meaningful analysis
                    continue
                    
                values = metric_data[metric_name].values
                mean_val = np.mean(values)
                std_val = np.std(values)
                
                # Only include metrics with sufficient data
                if not np.isnan(mean_val) and not np.isnan(std_val) and std_val > 0:
                    deviations['metrics'][metric_name] = {
                        'mean': float(mean_val),
                        'std': float(std_val),
                        'min': float(np.min(values)),
                        'max': float(np.max(values)),
                        'days': len(values)
                    }
                    
                    # Find significant deviations (> 1.5 standard deviations)
                    for i, row in metric_data.iterrows():
                        z_score = (row[metric_name] - mean_val) / std_val if std_val > 0 else 0
                        
                        if abs(z_score) > 1.5:
                            deviation = {
                                'date': str(row['date']),
                                'metric': metric_name,
                                'value': float(row[metric_name]),
                                'z_score': float(z_score),
                                'direction': 'above' if z_score > 0 else 'below'
                            }
                            deviations['significant_changes'].append(deviation)
            
            # Correlate with meals if available
            if processed_meals is not None and not processed_meals.empty:
                # Group deviations by date
                deviation_dates = set([d['date'] for d in deviations['significant_changes']])
                
                # Check for meals on deviation dates
                for date_str in deviation_dates:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        day_meals = processed_meals[processed_meals['date'] == date_obj]
                        
                        if not day_meals.empty:
                            # Find deviations on this date
                            day_deviations = [d for d in deviations['significant_changes'] if d['date'] == date_str]
                            
                            for meal_idx, meal_row in day_meals.iterrows():
                                meal_correlation = {
                                    'date': date_str,
                                    'meal': meal_row['dish'] if 'dish' in meal_row else 'Unknown',
                                    'meal_time': str(meal_row['time']) if 'time' in meal_row else 'Unknown',
                                    'deviating_metrics': [d['metric'] for d in day_deviations]
                                }
                                deviations['meal_correlations'].append(meal_correlation)
                    except Exception as e:
                        self.logger.warning(f"Error processing meals for date {date_str}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Error in deviation analysis: {str(e)}")
            
        return deviations
        self.rolling_window = kwargs.get('rolling_window', 14)  # 14-day rolling window
    
    def process(self, data: HealthDataCollection) -> Dict:
        """
        Perform correlation analysis for all participants.
        
        Parameters
        ----------
        data : HealthDataCollection
            Cleaned health data collection
            
        Returns
        -------
        Dict
            Correlation analysis results for all participants
        """
        results = {}
        
        for participant_id in data.get_participants():
            self.logger.info(f"Analyzing correlations for participant: {participant_id}")
            
            participant_data = data.get_participant_data(participant_id)
            participant_results = self._analyze_participant_correlations(
                participant_data, participant_id
            )
            
            if participant_results:
                results[participant_id] = participant_results
        
        return results
    
    def _analyze_participant_correlations(
        self, 
        records: List[HealthDataRecord], 
        participant_id: str
    ) -> Dict:
        """Analyze correlations for a single participant"""
        
        # Filter good quality data
        good_records = [r for r in records if r.quality_flag == 'good']
        
        if not good_records:
            return {}
        
        # Create daily aggregated DataFrame
        daily_df = self._create_daily_dataframe(good_records)
        
        if daily_df.empty or len(daily_df) < self.min_days:
            self.logger.warning(f"Insufficient data for {participant_id}: {len(daily_df)} days")
            return {}
        
        analysis = {
            'data_summary': {
                'date_range': {
                    'start': daily_df.index.min().strftime('%Y-%m-%d'),
                    'end': daily_df.index.max().strftime('%Y-%m-%d'),
                },
                'total_days': len(daily_df),
                'available_metrics': [col for col in daily_df.columns if not daily_df[col].isna().all()],
            },
            'daily_correlations': self._compute_daily_correlations(daily_df),
            'lag_correlations': self._compute_lag_correlations(daily_df),
            'rolling_correlations': self._compute_rolling_correlations(daily_df),
            'anomaly_analysis': self._analyze_anomalies(daily_df, good_records),
        }
        
        return analysis
    
    def _create_daily_dataframe(self, records: List[HealthDataRecord]) -> pd.DataFrame:
        """Create daily aggregated DataFrame from records"""
        
        # Group records by date and metric
        daily_data = {}
        
        for record in records:
            date = record.datetime.date()
            metric = record.metric_type
            
            if date not in daily_data:
                daily_data[date] = {}
            
            # Aggregate multiple readings per day
            if metric not in daily_data[date]:
                daily_data[date][metric] = []
            
            daily_data[date][metric].append(record.value_1)
        
        # Create DataFrame with daily averages
        df_data = []
        for date, metrics in daily_data.items():
            row = {'date': date}
            for metric, values in metrics.items():
                # Use mean for most metrics, sum for steps
                if metric == 'steps':
                    row[metric] = np.sum(values)  # Daily total steps
                else:
                    row[metric] = np.mean(values)  # Daily average
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        if df.empty:
            return df
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Sort by date
        df.sort_index(inplace=True)
        
        return df
    
    def _compute_daily_correlations(self, daily_df: pd.DataFrame) -> Dict:
        """Compute same-day correlations between metrics"""
        
        correlations = {}
        
        for metric1, metric2 in self.CORRELATION_PAIRS:
            if metric1 not in daily_df.columns or metric2 not in daily_df.columns:
                continue
            
            # Get valid pairs (both metrics available on same day)
            valid_mask = daily_df[metric1].notna() & daily_df[metric2].notna()
            valid_data = daily_df[valid_mask]
            
            if len(valid_data) < 5:  # Need minimum 5 days
                continue
            
            values1 = valid_data[metric1].values
            values2 = valid_data[metric2].values
            
            try:
                # Pearson correlation
                pearson_r, pearson_p = pearsonr(values1, values2)
                
                # Spearman correlation
                spearman_r, spearman_p = spearmanr(values1, values2)
                
                # Confidence level and interpretation
                confidence = self._get_confidence_level(len(valid_data), max(abs(pearson_r), abs(spearman_r)))
                interpretation = self._interpret_correlation(pearson_r, pearson_p, spearman_r, spearman_p)
                
                correlations[f"{metric1}_vs_{metric2}"] = {
                    'n_days': len(valid_data),
                    'pearson': {
                        'r': round(pearson_r, 3),
                        'p_value': round(pearson_p, 4),
                        'significant': pearson_p < 0.05,
                    },
                    'spearman': {
                        'r': round(spearman_r, 3),
                        'p_value': round(spearman_p, 4),
                        'significant': spearman_p < 0.05,
                    },
                    'confidence': confidence,
                    'interpretation': interpretation,
                }
                
            except Exception as e:
                self.logger.warning(f"Failed to compute correlation for {metric1} vs {metric2}: {e}")
        
        return correlations
    
    def _compute_lag_correlations(self, daily_df: pd.DataFrame) -> Dict:
        """Compute lag-1 correlations (today's metric vs tomorrow's effect)"""
        
        lag_correlations = {}
        
        for metric1, metric2 in self.CORRELATION_PAIRS:
            if metric1 not in daily_df.columns or metric2 not in daily_df.columns:
                continue
            
            # Create lag-1 data (metric1 today vs metric2 tomorrow)
            df_lag = daily_df[[metric1, metric2]].copy()
            df_lag[f'{metric2}_next'] = df_lag[metric2].shift(-1)  # Tomorrow's value
            
            # Get valid pairs
            valid_mask = df_lag[metric1].notna() & df_lag[f'{metric2}_next'].notna()
            valid_data = df_lag[valid_mask]
            
            if len(valid_data) < 5:
                continue
            
            values1 = valid_data[metric1].values
            values2 = valid_data[f'{metric2}_next'].values
            
            try:
                pearson_r, pearson_p = pearsonr(values1, values2)
                spearman_r, spearman_p = spearmanr(values1, values2)
                
                confidence = self._get_confidence_level(len(valid_data), max(abs(pearson_r), abs(spearman_r)))
                interpretation = self._interpret_lag_correlation(metric1, metric2, pearson_r, pearson_p)
                
                lag_correlations[f"{metric1}_to_{metric2}_next_day"] = {
                    'n_days': len(valid_data),
                    'pearson': {
                        'r': round(pearson_r, 3),
                        'p_value': round(pearson_p, 4),
                        'significant': pearson_p < 0.05,
                    },
                    'spearman': {
                        'r': round(spearman_r, 3),
                        'p_value': round(spearman_p, 4),
                        'significant': spearman_p < 0.05,
                    },
                    'confidence': confidence,
                    'interpretation': interpretation,
                }
                
            except Exception as e:
                self.logger.warning(f"Failed to compute lag correlation for {metric1} -> {metric2}: {e}")
        
        return lag_correlations
    
    def _compute_rolling_correlations(self, daily_df: pd.DataFrame) -> Dict:
        """Compute correlations using 14-day rolling windows"""
        
        if len(daily_df) < self.rolling_window + 5:  # Need extra days for meaningful analysis
            return {}
        
        rolling_results = {}
        
        for metric1, metric2 in self.CORRELATION_PAIRS:
            if metric1 not in daily_df.columns or metric2 not in daily_df.columns:
                continue
            
            rolling_correlations = []
            
            for i in range(self.rolling_window, len(daily_df)):
                window_data = daily_df.iloc[i-self.rolling_window:i]
                
                # Check if we have enough valid data in this window
                valid_mask = window_data[metric1].notna() & window_data[metric2].notna()
                valid_count = valid_mask.sum()
                
                if valid_count < 7:  # Need at least 7 days in window
                    rolling_correlations.append(np.nan)
                    continue
                
                values1 = window_data[metric1][valid_mask].values
                values2 = window_data[metric2][valid_mask].values
                
                try:
                    pearson_r, _ = pearsonr(values1, values2)
                    rolling_correlations.append(pearson_r)
                except:
                    rolling_correlations.append(np.nan)
            
            if any(not np.isnan(r) for r in rolling_correlations):
                rolling_results[f"{metric1}_vs_{metric2}"] = {
                    'correlations': [round(r, 3) if not np.isnan(r) else None for r in rolling_correlations],
                    'mean_correlation': round(np.nanmean(rolling_correlations), 3),
                    'std_correlation': round(np.nanstd(rolling_correlations), 3),
                    'trend_analysis': self._analyze_correlation_trend(rolling_correlations),
                }
        
        return rolling_results
    
    def _analyze_anomalies(self, daily_df: pd.DataFrame, records: List[HealthDataRecord]) -> Dict:
        """Analyze anomalous days and recovery patterns"""
        
        anomalies = {}
        
        for metric in daily_df.columns:
            if daily_df[metric].isna().all():
                continue
            
            values = daily_df[metric].dropna()
            if len(values) < 7:
                continue
            
            # Detect anomalies using IQR method
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 2.0 * IQR  # More conservative threshold
            upper_bound = Q3 + 2.0 * IQR
            
            anomaly_mask = (values < lower_bound) | (values > upper_bound)
            anomaly_dates = values[anomaly_mask].index.tolist()
            
            if not anomaly_dates:
                continue
            
            # Analyze recovery patterns
            recovery_analysis = self._analyze_recovery_patterns(daily_df, metric, anomaly_dates)
            
            # Generate insights
            insights = self._generate_anomaly_insights(metric, values, anomaly_dates, recovery_analysis)
            
            anomalies[metric] = {
                'anomaly_dates': [date.strftime('%Y-%m-%d') for date in anomaly_dates],
                'anomaly_count': len(anomaly_dates),
                'anomaly_percentage': round((len(anomaly_dates) / len(values)) * 100, 1),
                'normal_range': {
                    'lower': round(lower_bound, 2),
                    'upper': round(upper_bound, 2),
                },
                'recovery_analysis': recovery_analysis,
                'insights': insights,
            }
        
        return anomalies
    
    def _analyze_recovery_patterns(
        self, 
        daily_df: pd.DataFrame, 
        metric: str, 
        anomaly_dates: List[datetime]
    ) -> Dict:
        """Analyze how quickly metrics recover after anomalies"""
        
        recovery_times = []
        
        for anomaly_date in anomaly_dates:
            # Look for recovery in next 7 days
            for days_after in range(1, 8):
                recovery_date = anomaly_date + timedelta(days=days_after)
                
                if recovery_date not in daily_df.index:
                    break
                
                recovery_value = daily_df.loc[recovery_date, metric]
                if pd.isna(recovery_value):
                    continue
                
                # Check if value is back in normal range
                values = daily_df[metric].dropna()
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                
                if Q1 - 1.5 * IQR <= recovery_value <= Q3 + 1.5 * IQR:
                    recovery_times.append(days_after)
                    break
        
        if recovery_times:
            return {
                'mean_recovery_days': round(np.mean(recovery_times), 1),
                'median_recovery_days': round(np.median(recovery_times), 1),
                'recovery_rate': round((len(recovery_times) / len(anomaly_dates)) * 100, 1),
            }
        else:
            return {
                'mean_recovery_days': None,
                'median_recovery_days': None,
                'recovery_rate': 0.0,
            }
    
    def _get_confidence_level(self, n_days: int, correlation: float) -> str:
        """Get confidence level description for correlation"""
        
        if n_days >= 30 and abs(correlation) >= 0.5:
            return "solid"
        elif n_days >= 14 and abs(correlation) >= 0.3:
            return "pretty sure"
        elif abs(correlation) >= 0.2:
            return "might be a thing"
        else:
            return "not confident"
    
    def _interpret_correlation(
        self, 
        pearson_r: float, 
        pearson_p: float, 
        spearman_r: float, 
        spearman_p: float
    ) -> str:
        """Generate human-readable interpretation of correlation"""
        
        # Use stronger correlation
        r = pearson_r if abs(pearson_r) >= abs(spearman_r) else spearman_r
        p = pearson_p if abs(pearson_r) >= abs(spearman_r) else spearman_p
        
        if p >= 0.05:
            return "No significant relationship detected"
        
        strength = ""
        if abs(r) >= 0.7:
            strength = "strong"
        elif abs(r) >= 0.5:
            strength = "moderate"
        elif abs(r) >= 0.3:
            strength = "weak"
        else:
            strength = "very weak"
        
        direction = "positive" if r > 0 else "negative"
        
        return f"{strength.capitalize()} {direction} correlation"
    
    def _interpret_lag_correlation(
        self, 
        metric1: str, 
        metric2: str, 
        r: float, 
        p: float
    ) -> str:
        """Generate interpretation for lag correlations"""
        
        if p >= 0.05:
            return f"No significant next-day effect of {metric1} on {metric2}"
        
        direction = "increases" if r > 0 else "decreases"
        strength = "strongly" if abs(r) >= 0.5 else "moderately" if abs(r) >= 0.3 else "slightly"
        
        return f"Higher {metric1} today {strength} {direction} {metric2} tomorrow"
    
    def _analyze_correlation_trend(self, rolling_correlations: List[float]) -> Dict:
        """Analyze trend in rolling correlations"""
        
        valid_correlations = [r for r in rolling_correlations if not np.isnan(r)]
        
        if len(valid_correlations) < 3:
            return {'trend': 'insufficient_data'}
        
        # Simple trend analysis using linear regression
        x = np.arange(len(valid_correlations))
        y = np.array(valid_correlations)
        
        try:
            slope, intercept = np.polyfit(x, y, 1)
            
            if abs(slope) < 0.001:
                trend = "stable"
            elif slope > 0.005:
                trend = "strengthening"
            elif slope < -0.005:
                trend = "weakening"
            else:
                trend = "stable"
            
            return {
                'trend': trend,
                'slope': round(slope, 4),
                'strength_change': round(slope * len(valid_correlations), 3),
            }
            
        except:
            return {'trend': 'unstable'}
    
    def _generate_anomaly_insights(
        self, 
        metric: str, 
        values: pd.Series, 
        anomaly_dates: List[datetime], 
        recovery_analysis: Dict
    ) -> List[str]:
        """Generate insights about anomalies"""
        
        insights = []
        
        # Frequency insight
        anomaly_pct = (len(anomaly_dates) / len(values)) * 100
        if anomaly_pct > 15:
            insights.append(f"Frequent {metric} anomalies detected ({anomaly_pct:.0f}% of days)")
        elif anomaly_pct > 5:
            insights.append(f"Occasional {metric} anomalies detected ({anomaly_pct:.0f}% of days)")
        else:
            insights.append(f"Rare {metric} anomalies detected ({anomaly_pct:.0f}% of days)")
        
        # Recovery insight
        if recovery_analysis['recovery_rate'] > 80:
            insights.append(f"Quick recovery typical (average {recovery_analysis['mean_recovery_days']:.0f} days)")
        elif recovery_analysis['recovery_rate'] > 50:
            insights.append(f"Moderate recovery patterns (average {recovery_analysis['mean_recovery_days']:.0f} days)")
        else:
            insights.append("Slow or incomplete recovery from anomalies")
        
        # Clustering insight
        if len(anomaly_dates) > 1:
            time_gaps = [(anomaly_dates[i] - anomaly_dates[i-1]).days 
                        for i in range(1, len(anomaly_dates))]
            clustered = sum(1 for gap in time_gaps if gap <= 3)
            
            if clustered > len(time_gaps) * 0.5:
                insights.append("Anomalies tend to cluster together")
        
        return insights
    
    def _analyze_correlation_trend(self, rolling_correlations: List[float]) -> Dict:
        """Analyze trend in rolling correlations over time"""
        
        valid_correlations = [r for r in rolling_correlations if not np.isnan(r)]
        
        if len(valid_correlations) < 3:
            return {'trend': 'insufficient_data'}
        
        # Simple trend analysis using linear regression
        x = np.arange(len(valid_correlations))
        y = np.array(valid_correlations)
        
        try:
            slope, intercept = np.polyfit(x, y, 1)
            
            if abs(slope) < 0.001:
                trend = "stable"
            elif slope > 0.005:
                trend = "strengthening"
            elif slope < -0.005:
                trend = "weakening"
            else:
                trend = "stable"
            
            return {
                'trend': trend,
                'slope': round(slope, 4),
                'strength_change': round(slope * len(valid_correlations), 3),
            }
            
        except:
            return {'trend': 'unstable'}


def analyze_participant_correlations(
    data: HealthDataCollection, 
    output_dir: Path = None
) -> Dict:
    """
    Convenience function to analyze correlations for all participants.
    
    Parameters
    ----------
    data : HealthDataCollection
        Cleaned health data collection
    output_dir : Path, optional
        Directory to save individual participant results
        
    Returns
    -------
    Dict
        Correlation analysis results for all participants
    """
    engine = CorrelationEngine()
    results = engine.process(data)
    
    # Save individual participant files if output directory provided
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for participant_id, analysis in results.items():
            output_file = output_dir / f"patient-{participant_id.replace('participant-', '')}.json"
            
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
    
    return results


def generate_correlation_analysis(data: HealthDataCollection) -> Dict:
    """
    Generate correlation analysis for the main pipeline.
    
    Parameters
    ----------
    data : HealthDataCollection
        Cleaned health data collection
        
    Returns
    -------
    Dict
        Correlation analysis results for all participants
    """
    return analyze_participant_correlations(data)


def analyze_deviations(data_collection, meals_data=None, thresholds=None):
    """
    Analyze significant deviations in physio metrics and correlate with meals.
    
    Parameters
    ----------
    data_collection : HealthDataCollection
        Clean health data collection
    meals_data : pd.DataFrame, optional
        Meals data
    thresholds : dict, optional
        Thresholds for significant deviations
        
    Returns
    -------
    list
        List of deviations with associated meals
    """
    from wearables.src.correlation_engine import CorrelationEngine
    import logging
    
    logger = logging.getLogger('deviation_analysis')
    engine = CorrelationEngine()
    
    if thresholds is None:
        thresholds = {
            'bp_systolic': {'low': 90, 'high': 140},
            'bp_diastolic': {'low': 60, 'high': 90},
            'hr': {'low': 60, 'high': 100},
            'temp': {'low': 36.1, 'high': 37.5},
            'spo2': {'low': 95, 'high': 100},
            'sleep': {'low': 6, 'high': 9},
            'steps': {'low': 5000, 'high': 15000}
        }
    
    try:
        # Filter good quality data
        good_records = [r for r in data_collection.records if r.quality_flag == 'good']
        
        if not good_records:
            logger.warning("No good quality records for deviation analysis")
            return []
        
        # Create daily aggregated DataFrame
        daily_df = engine._create_daily_dataframe(good_records)
        
        if daily_df.empty or len(daily_df) < 7:  # Need at least a week of data
            logger.warning(f"Insufficient data for deviation analysis: {len(daily_df)} days")
            return []
        
        # Calculate baselines (averages)
        baselines = daily_df.mean()
        
        # Process meals data if provided
        meals_by_date = {}
        if meals_data is not None and 'time' in meals_data.columns and 'dish' in meals_data.columns:
            try:
                # Convert time to datetime
                meals_data = meals_data.copy()
                meals_data['date'] = pd.to_datetime(meals_data['time'], unit='ms').dt.date
                
                # Group by date
                for date, group in meals_data.groupby('date'):
                    meals_by_date[date] = group['dish'].tolist()
            except Exception as e:
                logger.error(f"Error processing meals data: {str(e)}")
        
        # Find deviations
        deviations = []
        
        for date_idx in daily_df.index:
            date_str = date_idx.strftime('%Y-%m-%d')
            date_obj = date_idx.date()
            daily_deviations = []
            
            # Check each metric for deviations
            for metric in daily_df.columns:
                if metric not in baselines or pd.isna(daily_df.loc[date_idx, metric]):
                    continue
                
                value = daily_df.loc[date_idx, metric]
                baseline = baselines[metric]
                
                # Calculate deviation percentage
                deviation_pct = ((value - baseline) / baseline) * 100 if baseline != 0 else 0
                
                # Check if value is outside thresholds
                threshold_deviation = False
                metric_key = None
                for key in thresholds.keys():
                    if key in metric.lower():
                        metric_key = key
                        break
                        
                if metric_key and metric_key in thresholds:
                    if value < thresholds[metric_key]['low']:
                        threshold_deviation = True
                    elif value > thresholds[metric_key]['high']:
                        threshold_deviation = True
                
                # Add significant deviations (>10% or outside thresholds)
                if abs(deviation_pct) > 10 or threshold_deviation:
                    daily_deviations.append({
                        'metric': metric,
                        'value': value,
                        'baseline': baseline,
                        'deviation_pct': deviation_pct,
                        'outside_threshold': threshold_deviation
                    })
            
            # If we have deviations, add with meals data
            if daily_deviations:
                meals_list = meals_by_date.get(date_obj, [])
                
                deviations.append({
                    'date': date_str,
                    'deviations': daily_deviations,
                    'meals': meals_list
                })
        
        logger.info(f"Deviation analysis complete. Found {len(deviations)} days with significant deviations")
        return deviations
        
    except Exception as e:
        logger.error(f"Error in deviation analysis: {str(e)}")
        return []


if __name__ == "__main__":
    # Example usage
    from .data_loader import load_goqii_data
    from .data_cleaner import clean_goqii_data
    import sys
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./processed/participant/")
    else:
        input_path = "./input"
        output_path = Path("./processed/participant/")
    
    print(f"Analyzing correlations from: {input_path}")
    
    try:
        # Load and clean data
        raw_data, _ = load_goqii_data(input_path)
        cleaned_data, _ = clean_goqii_data(raw_data)
        
        # Analyze correlations
        results = analyze_participant_correlations(cleaned_data, output_path)
        
        print(f"Correlation analysis complete for {len(results)} participants")
        
        # Display sample insights
        for participant_id, analysis in list(results.items())[:2]:  # First 2 participants
            print(f"\n{participant_id} sample insights:")
            if 'anomaly_analysis' in analysis:
                for metric, anomaly_data in analysis['anomaly_analysis'].items():
                    for insight in anomaly_data.get('insights', []):
                        print(f"  • {insight}")
            
    except Exception as e:
        print(f"Error analyzing correlations: {e}")
        sys.exit(1)
