"""
Participant insights generator for GOQII Health Data EDA Protocol

Generates personalized health insights including:
- Health baseline summaries
- Data-driven insights with actual numbers
- Anomaly detection with recovery messages
- Personalized recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
from scipy import stats
import warnings

from .core import HealthDataRecord, HealthDataCollection, BaseProcessor


class HealthBaselineAnalyzer(BaseProcessor):
    """
    Analyzes individual health baselines and normal ranges.
    """
    
    def process(self, participant_data: List[HealthDataRecord]) -> Dict:
        """
        Analyze health baseline for a single participant.
        
        Parameters
        ----------
        participant_data : List[HealthDataRecord]
            All health records for one participant
            
        Returns
        -------
        Dict
            Health baseline analysis
        """
        good_data = [r for r in participant_data if r.quality_flag == 'good']
        
        if not good_data:
            return {}
        
        baselines = {}
        
        # Group by metric type
        by_metric = {}
        for record in good_data:
            if record.metric_type not in by_metric:
                by_metric[record.metric_type] = []
            by_metric[record.metric_type].append(record)
        
        for metric_type, records in by_metric.items():
            if len(records) < 3:  # Need minimum data
                continue
            
            values = [r.value_1 for r in records]
            baseline = self._compute_baseline_stats(values, metric_type)
            
            # Add secondary value analysis if available
            if records[0].value_2 is not None:
                secondary_values = [r.value_2 for r in records if r.value_2 is not None]
                if secondary_values:
                    baseline['secondary'] = self._compute_baseline_stats(
                        secondary_values, 
                        f"{metric_type}_secondary"
                    )
            
            # Add temporal patterns
            baseline['temporal_patterns'] = self._analyze_temporal_patterns(records)
            
            baselines[metric_type] = baseline
        
        return baselines
    
    def _compute_baseline_stats(self, values: List[float], metric_type: str) -> Dict:
        """Compute baseline statistics for a metric"""
        
        values_array = np.array(values)
        
        baseline = {
            'count': len(values),
            'mean': round(np.mean(values_array), 1),
            'median': round(np.median(values_array), 1),
            'std': round(np.std(values_array), 2),
            'normal_range': {
                'lower': round(np.percentile(values_array, 10), 1),  # 10th percentile
                'upper': round(np.percentile(values_array, 90), 1),  # 90th percentile
            },
            'percentiles': {
                'p25': round(np.percentile(values_array, 25), 1),
                'p75': round(np.percentile(values_array, 75), 1),
            }
        }
        
        # Add interpretation based on clinical guidelines
        baseline['interpretation'] = self._interpret_baseline(baseline, metric_type)
        
        return baseline
    
    def _analyze_temporal_patterns(self, records: List[HealthDataRecord]) -> Dict:
        """Analyze temporal patterns in the data"""
        
        # Group by hour of day
        hourly_data = {}
        for record in records:
            hour = record.datetime.hour
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(record.value_1)
        
        # Find peak hours
        hourly_means = {hour: np.mean(values) for hour, values in hourly_data.items() if len(values) >= 2}
        
        peak_hour = max(hourly_means, key=hourly_means.get) if hourly_means else None
        low_hour = min(hourly_means, key=hourly_means.get) if hourly_means else None
        
        # Group by day of week
        daily_data = {}
        for record in records:
            day = record.datetime.strftime('%A')
            if day not in daily_data:
                daily_data[day] = []
            daily_data[day].append(record.value_1)
        
        daily_means = {day: np.mean(values) for day, values in daily_data.items() if len(values) >= 2}
        
        return {
            'hourly_patterns': {
                'peak_hour': peak_hour,
                'peak_value': round(hourly_means[peak_hour], 1) if peak_hour else None,
                'low_hour': low_hour,
                'low_value': round(hourly_means[low_hour], 1) if low_hour else None,
            },
            'weekly_patterns': daily_means,
        }
    
    def _interpret_baseline(self, baseline: Dict, metric_type: str) -> str:
        """Provide clinical interpretation of baseline values"""
        
        mean_val = baseline['mean']
        
        if metric_type == 'bp':
            if mean_val < 120:
                return "Normal blood pressure range"
            elif mean_val < 130:
                return "Elevated blood pressure"
            elif mean_val < 140:
                return "Stage 1 hypertension range"
            else:
                return "Stage 2 hypertension range"
        
        elif metric_type == 'hr':
            if mean_val < 60:
                return "Below normal resting heart rate (bradycardia)"
            elif mean_val < 100:
                return "Normal resting heart rate"
            else:
                return "Elevated resting heart rate (tachycardia)"
        
        elif metric_type == 'spo2':
            if mean_val >= 95:
                return "Normal oxygen saturation"
            elif mean_val >= 90:
                return "Borderline oxygen saturation"
            else:
                return "Low oxygen saturation"
        
        elif metric_type == 'temp':
            if 97.0 <= mean_val <= 99.0:
                return "Normal body temperature"
            elif mean_val > 99.0:
                return "Slightly elevated temperature"
            else:
                return "Slightly low temperature"
        
        elif metric_type == 'sleep':
            if 7 <= mean_val <= 9:
                return "Optimal sleep duration"
            elif mean_val < 7:
                return "Below recommended sleep duration"
            else:
                return "Above typical sleep duration"
        
        elif metric_type == 'steps':
            if mean_val >= 10000:
                return "Highly active lifestyle"
            elif mean_val >= 7500:
                return "Moderately active lifestyle"
            elif mean_val >= 5000:
                return "Somewhat active lifestyle"
            else:
                return "Sedentary lifestyle"
        
        else:
            return "Within measured range"


class PersonalizedInsightsGenerator(BaseProcessor):
    """
    Generates personalized health insights with specific numbers and recommendations.
    """
    
    def process(self, analysis_data: Dict) -> Dict:
        """
        Generate personalized insights from correlation and baseline analysis.
        
        Parameters
        ----------
        analysis_data : Dict
            Combined analysis data including baselines and correlations
            
        Returns
        -------
        Dict
            Personalized insights and recommendations
        """
        insights = {
            'health_summary': self._generate_health_summary(analysis_data),
            'key_findings': self._generate_key_findings(analysis_data),
            'behavioral_insights': self._generate_behavioral_insights(analysis_data),
            'recommendations': self._generate_recommendations(analysis_data),
            'progress_tracking': self._generate_progress_insights(analysis_data),
        }
        
        return insights
    
    def _generate_health_summary(self, data: Dict) -> Dict:
        """Generate overall health summary"""
        
        baselines = data.get('baselines', {})
        summary = {
            'monitoring_period': data.get('data_summary', {}).get('date_range', {}),
            'metrics_tracked': list(baselines.keys()),
            'data_quality_score': self._compute_data_quality_score(data),
        }
        
        # Generate summary statement
        statements = []
        
        for metric, baseline in baselines.items():
            if metric == 'bp':
                statements.append(f"Average blood pressure: {baseline['mean']}/{baseline.get('secondary', {}).get('mean', 'N/A')} mmHg")
            elif metric == 'hr':
                statements.append(f"Average heart rate: {baseline['mean']} bpm")
            elif metric == 'steps':
                statements.append(f"Average daily steps: {baseline['mean']:,.0f}")
            elif metric == 'sleep':
                statements.append(f"Average sleep: {baseline['mean']} hours per night")
            elif metric == 'spo2':
                statements.append(f"Average oxygen saturation: {baseline['mean']}%")
            elif metric == 'temp':
                statements.append(f"Average temperature: {baseline['mean']}°F")
        
        summary['health_metrics'] = statements
        
        return summary
    
    def _generate_key_findings(self, data: Dict) -> List[str]:
        """Generate key health findings with specific numbers"""
        
        findings = []
        baselines = data.get('baselines', {})
        correlations = data.get('daily_correlations', {})
        anomalies = data.get('anomaly_analysis', {})
        
        # Baseline findings
        for metric, baseline in baselines.items():
            interpretation = baseline.get('interpretation', '')
            mean_val = baseline['mean']
            
            if metric == 'bp' and mean_val >= 130:
                findings.append(f"Your average blood pressure of {mean_val} mmHg indicates elevated levels that may need attention")
            elif metric == 'hr' and mean_val > 100:
                findings.append(f"Your resting heart rate averages {mean_val} bpm, which is above the normal range (60-100 bpm)")
            elif metric == 'steps' and mean_val < 5000:
                findings.append(f"Your daily step count averages {mean_val:,.0f} steps, below the recommended 10,000 steps")
            elif metric == 'sleep' and mean_val < 7:
                findings.append(f"You're getting {mean_val} hours of sleep per night, below the recommended 7-9 hours")
            elif metric == 'spo2' and mean_val < 95:
                findings.append(f"Your oxygen saturation averages {mean_val}%, which may indicate respiratory concerns")
        
        # Correlation findings
        for correlation_name, corr_data in correlations.items():
            if corr_data.get('pearson', {}).get('significant', False):
                r_value = corr_data['pearson']['r']
                confidence = corr_data.get('confidence', 'uncertain')
                
                if abs(r_value) >= 0.5 and confidence in ['solid', 'pretty sure']:
                    metric1, metric2 = correlation_name.replace('_vs_', ' and ').split(' and ')
                    direction = "positively" if r_value > 0 else "negatively"
                    findings.append(f"Strong relationship found: your {metric1} and {metric2} are {direction} correlated (r={r_value:.2f})")
        
        # Anomaly findings
        for metric, anomaly_data in anomalies.items():
            anomaly_pct = anomaly_data.get('anomaly_percentage', 0)
            if anomaly_pct > 10:
                count = anomaly_data['anomaly_count']
                findings.append(f"Detected {count} unusual {metric} days ({anomaly_pct}% of monitoring period)")
        
        return findings
    
    def _generate_behavioral_insights(self, data: Dict) -> List[str]:
        """Generate behavioral insights from patterns"""
        
        insights = []
        baselines = data.get('baselines', {})
        lag_correlations = data.get('lag_correlations', {})
        
        # Temporal pattern insights
        for metric, baseline in baselines.items():
            temporal = baseline.get('temporal_patterns', {})
            hourly = temporal.get('hourly_patterns', {})
            
            if hourly.get('peak_hour') is not None:
                peak_hour = hourly['peak_hour']
                peak_val = hourly['peak_value']
                
                if metric == 'hr':
                    if 6 <= peak_hour <= 10:
                        insights.append(f"Your heart rate peaks in the morning around {peak_hour}:00 ({peak_val} bpm)")
                    elif 18 <= peak_hour <= 22:
                        insights.append(f"Your heart rate is highest in the evening around {peak_hour}:00 ({peak_val} bpm)")
                
                elif metric == 'bp':
                    if 6 <= peak_hour <= 10:
                        insights.append(f"Your blood pressure tends to be highest in the morning around {peak_hour}:00")
        
        # Lag effect insights
        for lag_name, lag_data in lag_correlations.items():
            if lag_data.get('pearson', {}).get('significant', False):
                interpretation = lag_data.get('interpretation', '')
                confidence = lag_data.get('confidence', '')
                
                if confidence in ['solid', 'pretty sure']:
                    insights.append(interpretation)
        
        # Weekly pattern insights
        for metric, baseline in baselines.items():
            weekly = baseline.get('temporal_patterns', {}).get('weekly_patterns', {})
            
            if len(weekly) >= 5:  # Have data for most days
                max_day = max(weekly, key=weekly.get)
                min_day = min(weekly, key=weekly.get)
                max_val = weekly[max_day]
                min_val = weekly[min_day]
                
                if metric == 'steps':
                    insights.append(f"You're most active on {max_day}s ({max_val:,.0f} steps) and least active on {min_day}s ({min_val:,.0f} steps)")
                elif metric == 'sleep':
                    if max_day in ['Saturday', 'Sunday'] and min_day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                        insights.append(f"You sleep longer on weekends ({max_val:.1f} hours on {max_day}s) vs weekdays ({min_val:.1f} hours on {min_day}s)")
        
        return insights
    
    def _generate_recommendations(self, data: Dict) -> List[Dict]:
        """Generate personalized recommendations"""
        
        recommendations = []
        baselines = data.get('baselines', {})
        correlations = data.get('daily_correlations', {})
        anomalies = data.get('anomaly_analysis', {})
        
        # Baseline-based recommendations
        for metric, baseline in baselines.items():
            mean_val = baseline['mean']
            
            if metric == 'bp' and mean_val >= 130:
                recommendations.append({
                    'category': 'Blood Pressure',
                    'priority': 'High',
                    'recommendation': 'Consider discussing your elevated blood pressure with a healthcare provider',
                    'action_items': [
                        'Reduce sodium intake to less than 2,300mg daily',
                        'Increase physical activity to 150 minutes per week',
                        'Monitor blood pressure regularly',
                    ],
                    'target': 'Reduce average to below 120 mmHg'
                })
            
            elif metric == 'steps' and mean_val < 7500:
                recommendations.append({
                    'category': 'Physical Activity',
                    'priority': 'Medium',
                    'recommendation': f'Increase daily activity from current {mean_val:,.0f} steps',
                    'action_items': [
                        'Set a goal of 500 additional steps per week',
                        'Take stairs instead of elevators',
                        'Park further away or get off transit one stop early',
                        'Take 5-minute walking breaks every hour',
                    ],
                    'target': 'Reach 10,000 steps daily'
                })
            
            elif metric == 'sleep' and mean_val < 7:
                recommendations.append({
                    'category': 'Sleep Quality',
                    'priority': 'High',
                    'recommendation': f'Increase sleep duration from current {mean_val} hours',
                    'action_items': [
                        'Set a consistent bedtime 30 minutes earlier',
                        'Create a relaxing bedtime routine',
                        'Avoid screens 1 hour before bed',
                        'Keep bedroom cool and dark',
                    ],
                    'target': 'Achieve 7-9 hours of sleep nightly'
                })
        
        # Correlation-based recommendations
        steps_sleep_corr = correlations.get('steps_vs_sleep', {})
        if steps_sleep_corr.get('pearson', {}).get('significant', False):
            r_value = steps_sleep_corr['pearson']['r']
            if r_value > 0.3:
                recommendations.append({
                    'category': 'Lifestyle Synergy',
                    'priority': 'Medium',
                    'recommendation': 'Your activity and sleep are positively connected',
                    'action_items': [
                        'Maintain consistent exercise routine for better sleep',
                        'Aim for morning or afternoon workouts',
                        'Track both metrics to optimize the relationship',
                    ],
                    'target': 'Leverage exercise for improved sleep quality'
                })
        
        # Anomaly-based recommendations
        for metric, anomaly_data in anomalies.items():
            recovery_rate = anomaly_data.get('recovery_analysis', {}).get('recovery_rate', 0)
            
            if recovery_rate < 50:
                recommendations.append({
                    'category': 'Health Monitoring',
                    'priority': 'Medium',
                    'recommendation': f'Improve {metric} recovery patterns',
                    'action_items': [
                        f'Monitor {metric} more closely during unusual periods',
                        'Identify triggers for abnormal readings',
                        'Develop strategies for faster recovery',
                    ],
                    'target': 'Achieve faster return to normal ranges'
                })
        
        # Sort by priority
        priority_order = {'High': 3, 'Medium': 2, 'Low': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return recommendations
    
    def _generate_progress_insights(self, data: Dict) -> Dict:
        """Generate progress tracking insights"""
        
        rolling_corr = data.get('rolling_correlations', {})
        anomalies = data.get('anomaly_analysis', {})
        
        progress = {
            'stability_trends': {},
            'improvement_areas': [],
            'concerning_trends': [],
        }
        
        # Analyze stability in correlations
        for corr_name, corr_data in rolling_corr.items():
            trend = corr_data.get('trend_analysis', {}).get('trend', '')
            
            if trend == 'strengthening':
                progress['improvement_areas'].append(f"Relationship between {corr_name.replace('_vs_', ' and ')} is getting stronger over time")
            elif trend == 'weakening':
                progress['concerning_trends'].append(f"Relationship between {corr_name.replace('_vs_', ' and ')} is weakening over time")
            else:
                progress['stability_trends'][corr_name] = 'stable'
        
        # Analyze anomaly patterns
        recent_anomalies = []
        for metric, anomaly_data in anomalies.items():
            anomaly_dates = anomaly_data.get('anomaly_dates', [])
            if anomaly_dates:
                # Check if recent anomalies (last 7 days of data)
                recent_count = 0
                for date_str in anomaly_dates[-7:]:  # Last few dates
                    recent_count += 1
                
                if recent_count > 0:
                    recent_anomalies.append(f"{recent_count} recent {metric} anomalies")
        
        if recent_anomalies:
            progress['concerning_trends'].extend(recent_anomalies)
        
        return progress
    
    def _compute_data_quality_score(self, data: Dict) -> int:
        """Compute overall data quality score (0-100)"""
        
        # Simple scoring based on available data
        baselines = data.get('baselines', {})
        
        if not baselines:
            return 0
        
        total_metrics = 6  # bp, sleep, steps, hr, spo2, temp
        available_metrics = len(baselines)
        
        base_score = (available_metrics / total_metrics) * 100
        
        # Bonus for good data quality
        total_records = sum(b.get('count', 0) for b in baselines.values())
        if total_records > 100:  # Good amount of data
            base_score = min(100, base_score * 1.1)
        
        return int(base_score)


class ParticipantInsightPipeline(BaseProcessor):
    """
    Complete pipeline for generating participant insights.
    """
    
    def process(self, data: Tuple[HealthDataCollection, str]) -> Dict:
        """
        Generate complete participant insights.
        
        Parameters
        ----------
        data : Tuple[HealthDataCollection, str]
            (health_data_collection, participant_id)
            
        Returns
        -------
        Dict
            Complete participant insights
        """
        collection, participant_id = data
        participant_data = collection.get_participant_data(participant_id)
        
        if not participant_data:
            return {}
        
        self.logger.info(f"Generating insights for {participant_id}")
        
        # Generate baseline analysis
        baseline_analyzer = HealthBaselineAnalyzer()
        baselines = baseline_analyzer.process(participant_data)
        
        # Load correlation analysis if available
        from .correlation_engine import CorrelationEngine
        corr_engine = CorrelationEngine()
        
        # Create mini collection for this participant
        participant_collection = HealthDataCollection()
        participant_collection.add_records(participant_data)
        
        corr_results = corr_engine.process(participant_collection)
        participant_correlations = corr_results.get(participant_id, {})
        
        # Combine analysis data
        combined_data = {
            'baselines': baselines,
            **participant_correlations  # Include all correlation analysis
        }
        
        # Generate insights
        insights_generator = PersonalizedInsightsGenerator()
        insights = insights_generator.process(combined_data)
        
        # Create final output
        result = {
            'participant_id': participant_id,
            'generated_at': datetime.now().isoformat(),
            'data_period': combined_data.get('data_summary', {}),
            'health_baselines': baselines,
            'correlations': {
                'daily': participant_correlations.get('daily_correlations', {}),
                'lag_effects': participant_correlations.get('lag_correlations', {}),
                'rolling_trends': participant_correlations.get('rolling_correlations', {}),
            },
            'anomalies': participant_correlations.get('anomaly_analysis', {}),
            'personalized_insights': insights,
        }
        
        return result


def generate_participant_insights(
    data: HealthDataCollection,
    output_dir: Path = None
) -> Dict[str, Dict]:
    """
    Generate insights for all participants.
    
    Parameters
    ----------
    data : HealthDataCollection
        Cleaned health data collection
    output_dir : Path, optional
        Directory to save individual participant insights
        
    Returns
    -------
    Dict[str, Dict]
        Insights for all participants
    """
    pipeline = ParticipantInsightPipeline()
    all_insights = {}
    
    for participant_id in data.get_participants():
        insights = pipeline.process((data, participant_id))
        
        if insights:
            all_insights[participant_id] = insights
            
            # Save individual file
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"patient-{participant_id.replace('participant-', '')}.json"
                
                with open(output_file, 'w') as f:
                    json.dump(insights, f, indent=2, default=str)
    
    return all_insights


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
    
    print(f"Generating participant insights from: {input_path}")
    
    try:
        # Load and clean data
        raw_data, _ = load_goqii_data(input_path)
        cleaned_data, _ = clean_goqii_data(raw_data)
        
        # Generate insights
        insights = generate_participant_insights(cleaned_data, output_path)
        
        print(f"Generated insights for {len(insights)} participants")
        
        # Display sample insights
        for participant_id, insight_data in list(insights.items())[:1]:  # First participant
            print(f"\n{participant_id} key findings:")
            key_findings = insight_data.get('personalized_insights', {}).get('key_findings', [])
            for finding in key_findings[:3]:  # First 3 findings
                print(f"  • {finding}")
            
            print(f"\nRecommendations:")
            recommendations = insight_data.get('personalized_insights', {}).get('recommendations', [])
            for rec in recommendations[:2]:  # First 2 recommendations
                print(f"  • {rec['recommendation']} (Priority: {rec['priority']})")
            
    except Exception as e:
        print(f"Error generating insights: {e}")
        sys.exit(1)
