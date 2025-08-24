"""
Researcher-facing analysis module for GOQII Health Data EDA Protocol

Provides technical insights including:
- Missingness ratios and compliance scores
- Noise analysis and quality control metrics
- Cohort-level summaries and correlations
- Weekly/seasonal trend analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import warnings

from .core import HealthDataRecord, HealthDataCollection, BaseProcessor


class MissingnessAnalyzer(BaseProcessor):
    """
    Analyzes data missingness patterns and compliance scores.
    """
    
    # Expected data collection frequencies (per day)
    EXPECTED_FREQUENCIES = {
        'bp': 2,      # 2 readings per day (morning/evening)
        'sleep': 1,   # 1 sleep record per day
        'steps': 1,   # 1 daily step count
        'hr': 24,     # Hourly heart rate readings
        'spo2': 8,    # Every 3 hours
        'temp': 12,   # Every 2 hours
    }
    
    def process(self, data: HealthDataCollection) -> Dict:
        """
        Analyze missingness patterns for all participants and metrics.
        
        Parameters
        ----------
        data : HealthDataCollection
            Health data collection
            
        Returns
        -------
        Dict
            Missingness analysis results
        """
        analysis = {}
        
        for participant_id in data.get_participants():
            analysis[participant_id] = self._analyze_participant_missingness(
                data, participant_id
            )
        
        # Add cohort-level summary
        analysis['cohort_summary'] = self._compute_cohort_missingness(analysis)
        
        return analysis
    
    def _analyze_participant_missingness(
        self, 
        data: HealthDataCollection, 
        participant_id: str
    ) -> Dict:
        """Analyze missingness for a single participant"""
        
        participant_data = data.get_participant_data(participant_id)
        
        if not participant_data:
            return {}
        
        # Get date range for this participant
        dates = [r.datetime.date() for r in participant_data]
        min_date, max_date = min(dates), max(dates)
        total_days = (max_date - min_date).days + 1
        
        # Analyze each metric
        metric_analysis = {}
        
        for metric_type in self.EXPECTED_FREQUENCIES.keys():
            metric_records = [r for r in participant_data if r.metric_type == metric_type]
            
            if not metric_records:
                metric_analysis[metric_type] = {
                    'missingness_ratio': 1.0,
                    'compliance_score': 0.0,
                    'expected_records': total_days * self.EXPECTED_FREQUENCIES[metric_type],
                    'actual_records': 0,
                    'good_records': 0,
                }
                continue
            
            # Calculate expected vs actual
            expected = total_days * self.EXPECTED_FREQUENCIES[metric_type]
            actual = len(metric_records)
            good_records = len([r for r in metric_records if r.quality_flag == 'good'])
            
            # Missingness ratio (0 = no missing data, 1 = all missing)
            missingness_ratio = max(0, (expected - actual) / expected)
            
            # Compliance score (0-100) based on good quality data
            compliance_score = (good_records / expected) * 100 if expected > 0 else 0
            compliance_score = min(100, compliance_score)  # Cap at 100%
            
            # Daily compliance analysis
            daily_compliance = self._analyze_daily_compliance(
                metric_records, metric_type, min_date, max_date
            )
            
            metric_analysis[metric_type] = {
                'missingness_ratio': round(missingness_ratio, 3),
                'compliance_score': round(compliance_score, 1),
                'expected_records': expected,
                'actual_records': actual,
                'good_records': good_records,
                'daily_compliance': daily_compliance,
            }
        
        return {
            'date_range': {
                'start': min_date.isoformat(),
                'end': max_date.isoformat(),
                'total_days': total_days,
            },
            'metrics': metric_analysis,
            'overall_compliance': self._compute_overall_compliance(metric_analysis),
        }
    
    def _analyze_daily_compliance(
        self, 
        records: List[HealthDataRecord],
        metric_type: str,
        min_date: datetime.date,
        max_date: datetime.date
    ) -> Dict:
        """Analyze compliance on a daily basis"""
        
        expected_per_day = self.EXPECTED_FREQUENCIES[metric_type]
        
        # Group records by date
        daily_records = {}
        for record in records:
            date_key = record.datetime.date()
            if date_key not in daily_records:
                daily_records[date_key] = []
            daily_records[date_key].append(record)
        
        # Analyze each day
        daily_stats = []
        current_date = min_date
        
        while current_date <= max_date:
            day_records = daily_records.get(current_date, [])
            good_records = [r for r in day_records if r.quality_flag == 'good']
            
            compliance_pct = (len(good_records) / expected_per_day) * 100 if expected_per_day > 0 else 0
            compliance_pct = min(100, compliance_pct)  # Cap at 100%
            
            daily_stats.append({
                'date': current_date.isoformat(),
                'expected': expected_per_day,
                'actual': len(day_records),
                'good': len(good_records),
                'compliance_percentage': round(compliance_pct, 1),
            })
            
            current_date += timedelta(days=1)
        
        # Calculate summary stats
        compliance_values = [d['compliance_percentage'] for d in daily_stats]
        
        return {
            'daily_details': daily_stats,
            'mean_compliance': round(np.mean(compliance_values), 1),
            'median_compliance': round(np.median(compliance_values), 1),
            'min_compliance': round(np.min(compliance_values), 1),
            'max_compliance': round(np.max(compliance_values), 1),
            'std_compliance': round(np.std(compliance_values), 1),
        }
    
    def _compute_overall_compliance(self, metric_analysis: Dict) -> Dict:
        """Compute overall compliance across all metrics"""
        
        if not metric_analysis:
            return {'score': 0, 'grade': 'F'}
        
        compliance_scores = [
            data['compliance_score'] 
            for data in metric_analysis.values() 
            if isinstance(data, dict) and 'compliance_score' in data
        ]
        
        if not compliance_scores:
            return {'score': 0, 'grade': 'F'}
        
        overall_score = np.mean(compliance_scores)
        
        # Assign letter grade
        if overall_score >= 90:
            grade = 'A'
        elif overall_score >= 80:
            grade = 'B'
        elif overall_score >= 70:
            grade = 'C'
        elif overall_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': round(overall_score, 1),
            'grade': grade,
            'metric_scores': {
                metric: data['compliance_score'] 
                for metric, data in metric_analysis.items()
                if isinstance(data, dict) and 'compliance_score' in data
            }
        }
    
    def _compute_cohort_missingness(self, participant_analyses: Dict) -> Dict:
        """Compute cohort-level missingness summary"""
        
        # Exclude cohort_summary if it exists in the input
        analyses = {k: v for k, v in participant_analyses.items() if k != 'cohort_summary'}
        
        if not analyses:
            return {}
        
        # Overall compliance distribution
        overall_scores = []
        for analysis in analyses.values():
            if 'overall_compliance' in analysis:
                overall_scores.append(analysis['overall_compliance']['score'])
        
        # Metric-wise compliance
        metric_compliance = {}
        for metric_type in self.EXPECTED_FREQUENCIES.keys():
            metric_scores = []
            for analysis in analyses.values():
                if 'metrics' in analysis and metric_type in analysis['metrics']:
                    metric_scores.append(analysis['metrics'][metric_type]['compliance_score'])
            
            if metric_scores:
                metric_compliance[metric_type] = {
                    'mean': round(np.mean(metric_scores), 1),
                    'median': round(np.median(metric_scores), 1),
                    'std': round(np.std(metric_scores), 1),
                    'quartiles': {
                        'q25': round(np.percentile(metric_scores, 25), 1),
                        'q75': round(np.percentile(metric_scores, 75), 1),
                    }
                }
        
        return {
            'overall_compliance_distribution': {
                'mean': round(np.mean(overall_scores), 1) if overall_scores else 0,
                'median': round(np.median(overall_scores), 1) if overall_scores else 0,
                'std': round(np.std(overall_scores), 1) if overall_scores else 0,
                'quartiles': {
                    'q25': round(np.percentile(overall_scores, 25), 1) if overall_scores else 0,
                    'q75': round(np.percentile(overall_scores, 75), 1) if overall_scores else 0,
                }
            },
            'metric_compliance_distribution': metric_compliance,
            'total_participants': len(analyses),
        }


class NoiseAnalyzer(BaseProcessor):
    """
    Analyzes data noise and trigger frequency patterns.
    """
    
    def process(self, data: HealthDataCollection) -> Dict:
        """
        Analyze noise patterns across all data.
        
        Parameters
        ----------
        data : HealthDataCollection
            Health data collection
            
        Returns
        -------
        Dict
            Noise analysis results
        """
        analysis = {}
        
        for metric_type in data.get_metric_types():
            metric_data = data.get_metric_data(metric_type)
            analysis[metric_type] = self._analyze_metric_noise(metric_data, metric_type)
        
        return analysis
    
    def _analyze_metric_noise(
        self, 
        records: List[HealthDataRecord], 
        metric_type: str
    ) -> Dict:
        """Analyze noise patterns for a specific metric"""
        
        if not records:
            return {}
        
        # Separate good vs noisy data
        good_records = [r for r in records if r.quality_flag == 'good']
        outlier_records = [r for r in records if r.quality_flag == 'outlier']
        
        analysis = {
            'total_records': len(records),
            'good_records': len(good_records),
            'outlier_records': len(outlier_records),
            'noise_ratio': len(outlier_records) / len(records) if records else 0,
        }
        
        if good_records:
            # Analyze variability in good data
            values = [r.value_1 for r in good_records]
            analysis['good_data_stats'] = {
                'mean': round(np.mean(values), 2),
                'std': round(np.std(values), 2),
                'coefficient_of_variation': round(np.std(values) / np.mean(values), 3) if np.mean(values) != 0 else 0,
                'range': round(np.max(values) - np.min(values), 2),
            }
        
        if outlier_records:
            # Analyze outlier patterns
            outlier_values = [r.value_1 for r in outlier_records]
            analysis['outlier_stats'] = {
                'mean': round(np.mean(outlier_values), 2),
                'std': round(np.std(outlier_values), 2),
                'range': round(np.max(outlier_values) - np.min(outlier_values), 2),
            }
            
            # Temporal clustering of outliers
            analysis['outlier_temporal_pattern'] = self._analyze_outlier_clustering(outlier_records)
        
        return analysis
    
    def _analyze_outlier_clustering(self, outlier_records: List[HealthDataRecord]) -> Dict:
        """Analyze if outliers cluster in time"""
        
        if len(outlier_records) < 2:
            return {'clustering_detected': False}
        
        # Sort by datetime
        sorted_records = sorted(outlier_records, key=lambda x: x.datetime)
        
        # Calculate time gaps between consecutive outliers
        time_gaps = []
        for i in range(1, len(sorted_records)):
            gap = sorted_records[i].datetime - sorted_records[i-1].datetime
            time_gaps.append(gap.total_seconds() / 3600)  # Convert to hours
        
        # Detect clustering (outliers within 24 hours of each other)
        clustered_outliers = sum(1 for gap in time_gaps if gap <= 24)
        clustering_ratio = clustered_outliers / len(time_gaps) if time_gaps else 0
        
        return {
            'clustering_detected': clustering_ratio > 0.3,  # If >30% are clustered
            'clustering_ratio': round(clustering_ratio, 3),
            'mean_gap_hours': round(np.mean(time_gaps), 1) if time_gaps else 0,
            'median_gap_hours': round(np.median(time_gaps), 1) if time_gaps else 0,
        }


class CohortAnalyzer(BaseProcessor):
    """
    Provides cohort-level analysis and insights.
    """
    
    def process(self, data: HealthDataCollection) -> Dict:
        """
        Perform comprehensive cohort analysis.
        
        Parameters
        ----------
        data : HealthDataCollection
            Health data collection
            
        Returns
        -------
        Dict
            Cohort analysis results
        """
        analysis = {
            'summary_statistics': self._compute_summary_statistics(data),
            'cross_metric_correlations': self._compute_cross_metric_correlations(data),
            'temporal_trends': self._analyze_temporal_trends(data),
            'cohort_insights': self._generate_cohort_insights(data),
        }
        
        return analysis
    
    def _compute_summary_statistics(self, data: HealthDataCollection) -> Dict:
        """Compute descriptive statistics for each metric"""
        
        stats = {}
        
        for metric_type in data.get_metric_types():
            metric_data = data.get_metric_data(metric_type)
            good_data = [r for r in metric_data if r.quality_flag == 'good']
            
            if not good_data:
                continue
            
            values = [r.value_1 for r in good_data]
            
            stats[metric_type] = {
                'count': len(values),
                'mean': round(np.mean(values), 2),
                'median': round(np.median(values), 2),
                'std': round(np.std(values), 2),
                'min': round(np.min(values), 2),
                'max': round(np.max(values), 2),
                'iqr': round(np.percentile(values, 75) - np.percentile(values, 25), 2),
                'percentiles': {
                    'p25': round(np.percentile(values, 25), 2),
                    'p50': round(np.percentile(values, 50), 2),
                    'p75': round(np.percentile(values, 75), 2),
                    'p90': round(np.percentile(values, 90), 2),
                    'p95': round(np.percentile(values, 95), 2),
                }
            }
            
            # Add secondary value stats if available
            if good_data[0].value_2 is not None:
                values_2 = [r.value_2 for r in good_data if r.value_2 is not None]
                if values_2:
                    stats[metric_type]['secondary_value'] = {
                        'mean': round(np.mean(values_2), 2),
                        'median': round(np.median(values_2), 2),
                        'std': round(np.std(values_2), 2),
                    }
        
        return stats
    
    def _compute_cross_metric_correlations(self, data: HealthDataCollection) -> Dict:
        """Compute correlations between different health metrics"""
        
        correlations = {}
        participants = data.get_participants()
        metric_types = data.get_metric_types()
        
        # Create participant-level aggregated data
        participant_metrics = {}
        for participant_id in participants:
            participant_data = data.get_participant_data(participant_id)
            good_data = [r for r in participant_data if r.quality_flag == 'good']
            
            metrics = {}
            for metric_type in metric_types:
                metric_records = [r for r in good_data if r.metric_type == metric_type]
                if metric_records:
                    metrics[metric_type] = np.mean([r.value_1 for r in metric_records])
            
            if len(metrics) >= 2:  # Need at least 2 metrics for correlation
                participant_metrics[participant_id] = metrics
        
        # Compute pairwise correlations
        for i, metric1 in enumerate(metric_types):
            for metric2 in metric_types[i+1:]:
                # Get participants who have both metrics
                values1, values2 = [], []
                
                for participant_id, metrics in participant_metrics.items():
                    if metric1 in metrics and metric2 in metrics:
                        values1.append(metrics[metric1])
                        values2.append(metrics[metric2])
                
                if len(values1) >= 5:  # Minimum 5 participants for meaningful correlation
                    try:
                        pearson_r, pearson_p = pearsonr(values1, values2)
                        spearman_r, spearman_p = spearmanr(values1, values2)
                        
                        correlations[f"{metric1}_vs_{metric2}"] = {
                            'n_participants': len(values1),
                            'pearson': {
                                'r': round(pearson_r, 3),
                                'p_value': round(pearson_p, 4),
                                'significant': pearson_p < 0.05,
                            },
                            'spearman': {
                                'r': round(spearman_r, 3),
                                'p_value': round(spearman_p, 4),
                                'significant': spearman_p < 0.05,
                            }
                        }
                    except Exception as e:
                        self.logger.warning(f"Failed to compute correlation for {metric1} vs {metric2}: {e}")
        
        return correlations
    
    def _analyze_temporal_trends(self, data: HealthDataCollection) -> Dict:
        """Analyze weekly and seasonal trends"""
        
        trends = {}
        
        for metric_type in data.get_metric_types():
            metric_data = [r for r in data.get_metric_data(metric_type) if r.quality_flag == 'good']
            
            if not metric_data:
                continue
            
            # Weekly trends
            weekly_data = {}
            for record in metric_data:
                week_day = record.datetime.strftime('%A')
                if week_day not in weekly_data:
                    weekly_data[week_day] = []
                weekly_data[week_day].append(record.value_1)
            
            weekly_means = {day: np.mean(values) for day, values in weekly_data.items()}
            
            # Seasonal trends (by month)
            monthly_data = {}
            for record in metric_data:
                month = record.datetime.strftime('%B')
                if month not in monthly_data:
                    monthly_data[month] = []
                monthly_data[month].append(record.value_1)
            
            monthly_means = {month: np.mean(values) for month, values in monthly_data.items()}
            
            trends[metric_type] = {
                'weekly_patterns': weekly_means,
                'monthly_patterns': monthly_means,
            }
        
        return trends
    
    def _generate_cohort_insights(self, data: HealthDataCollection) -> List[str]:
        """Generate human-readable insights about the cohort"""
        
        insights = []
        
        # Data completeness insights
        participants = data.get_participants()
        metrics = data.get_metric_types()
        
        insights.append(f"Cohort includes {len(participants)} participants with {len(metrics)} different health metrics.")
        
        # Quality insights
        total_records = len(data)
        good_records = len([r for r in data.records if r.quality_flag == 'good'])
        if total_records > 0:
            good_pct = (good_records / total_records) * 100
            insights.append(f"Overall data quality: {good_pct:.1f}% of records passed quality checks.")
        
        # Metric-specific insights
        for metric_type in metrics:
            metric_data = [r for r in data.get_metric_data(metric_type) if r.quality_flag == 'good']
            
            if not metric_data:
                continue
            
            values = [r.value_1 for r in metric_data]
            participants_with_metric = len(set(r.participant_id for r in metric_data))
            
            if metric_type == 'bp':
                high_bp_count = len([v for v in values if v >= 140])  # Systolic >= 140
                if high_bp_count > 0:
                    high_bp_pct = (high_bp_count / len(values)) * 100
                    insights.append(f"Blood pressure: {high_bp_pct:.1f}% of readings show elevated systolic pressure (≥140 mmHg).")
            
            elif metric_type == 'hr':
                mean_hr = np.mean(values)
                if mean_hr > 100:
                    insights.append(f"Heart rate: Cohort average of {mean_hr:.0f} bpm indicates elevated resting heart rate.")
                elif mean_hr < 60:
                    insights.append(f"Heart rate: Cohort average of {mean_hr:.0f} bpm suggests good cardiovascular fitness.")
            
            elif metric_type == 'steps':
                mean_steps = np.mean(values)
                active_days = len([v for v in values if v >= 10000])
                if active_days > 0:
                    active_pct = (active_days / len(values)) * 100
                    insights.append(f"Physical activity: {active_pct:.1f}% of days meet the 10,000 steps guideline.")
            
            elif metric_type == 'sleep':
                mean_sleep = np.mean(values)
                if mean_sleep < 7:
                    insights.append(f"Sleep: Cohort averages {mean_sleep:.1f} hours per night, below recommended 7-9 hours.")
                elif mean_sleep > 9:
                    insights.append(f"Sleep: Cohort averages {mean_sleep:.1f} hours per night, above typical range.")
        
        return insights


class TechnicalReportGenerator(BaseProcessor):
    """
    Generates comprehensive technical reports for researchers.
    """
    
    def process(self, data: HealthDataCollection) -> Dict:
        """
        Generate complete technical analysis report.
        
        Parameters
        ----------
        data : HealthDataCollection
            Cleaned health data collection
            
        Returns
        -------
        Dict
            Complete technical report
        """
        self.logger.info("Generating technical analysis report")
        
        # Run all analyses
        missingness_analyzer = MissingnessAnalyzer()
        noise_analyzer = NoiseAnalyzer()
        cohort_analyzer = CohortAnalyzer()
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_records': len(data),
                'total_participants': len(data.get_participants()),
                'metrics_analyzed': data.get_metric_types(),
            },
            'missingness_analysis': missingness_analyzer.process(data),
            'noise_analysis': noise_analyzer.process(data),
            'cohort_analysis': cohort_analyzer.process(data),
        }
        
        return report
    
    def save_report(self, report: Dict, output_path: Path):
        """Save technical report to JSON file"""
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Technical report saved to: {output_path}")


def analyze_goqii_data_technical(data: HealthDataCollection) -> Dict:
    """
    Convenience function to generate complete technical analysis.
    
    Parameters
    ----------
    data : HealthDataCollection
        Cleaned health data collection
        
    Returns
    -------
    Dict
        Complete technical analysis report
    """
    generator = TechnicalReportGenerator()
    return generator.process(data)


def generate_technical_analysis(data: HealthDataCollection) -> Dict:
    """
    Generate complete technical analysis for the main pipeline.
    
    Parameters
    ----------
    data : HealthDataCollection
        Cleaned health data collection
        
    Returns
    -------
    Dict
        Complete technical analysis report
    """
    return analyze_goqii_data_technical(data)


if __name__ == "__main__":
    # Example usage
    from .data_loader import load_goqii_data
    from .data_cleaner import clean_goqii_data
    import sys
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./processed/technical/technical_report.json")
    else:
        input_path = "./input"
        output_path = Path("./processed/technical/technical_report.json")
    
    print(f"Generating technical analysis from: {input_path}")
    
    try:
        # Load and clean data
        raw_data, _ = load_goqii_data(input_path)
        cleaned_data, _ = clean_goqii_data(raw_data)
        
        # Generate technical report
        report = analyze_goqii_data_technical(cleaned_data)
        
        # Save report
        generator = TechnicalReportGenerator()
        generator.save_report(report, output_path)
        
        # Display key insights
        cohort_insights = report['cohort_analysis']['cohort_insights']
        print("\nKey Cohort Insights:")
        for insight in cohort_insights:
            print(f"  • {insight}")
            
    except Exception as e:
        print(f"Error generating technical analysis: {e}")
        sys.exit(1)
