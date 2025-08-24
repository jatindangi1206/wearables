"""
HTML Dashboard Generator for GOQII Health Data EDA Protocol

Generates beautiful, responsive HTML dashboards with:
- Interactive charts and visualizations
- Dual output: Researcher and Participant views
- Correlation analysis displays
- Exportable reports
"""

import json
import base64
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from io import BytesIO

# Import plotting libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    plt.style.use('seaborn-v0_8')
except ImportError:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    plt.style.use('default')

from .core import HealthDataCollection, BaseProcessor


class ChartGenerator:
    """
    Generates interactive charts and visualizations.
    """
    
    @staticmethod
    def create_correlation_heatmap(correlations: Dict, title: str = "Correlation Matrix") -> str:
        """Create correlation heatmap as base64 image"""
        
        # Extract correlation data
        corr_data = {}
        metrics = set()
        
        for corr_name, corr_result in correlations.items():
            if 'pearson' in corr_result:
                metric1, metric2 = corr_name.replace('_vs_', '|').split('|')
                metrics.add(metric1)
                metrics.add(metric2)
                corr_data[(metric1, metric2)] = corr_result['pearson']['r']
        
        if not corr_data:
            return ""
        
        # Create correlation matrix
        metrics_list = sorted(list(metrics))
        n_metrics = len(metrics_list)
        corr_matrix = np.zeros((n_metrics, n_metrics))
        
        for i, metric1 in enumerate(metrics_list):
            for j, metric2 in enumerate(metrics_list):
                if i == j:
                    corr_matrix[i, j] = 1.0
                elif (metric1, metric2) in corr_data:
                    corr_matrix[i, j] = corr_data[(metric1, metric2)]
                elif (metric2, metric1) in corr_data:
                    corr_matrix[i, j] = corr_data[(metric2, metric1)]
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
        
        # Add labels
        ax.set_xticks(range(n_metrics))
        ax.set_yticks(range(n_metrics))
        ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics_list])
        ax.set_yticklabels([m.replace('_', ' ').title() for m in metrics_list])
        
        # Rotate labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Add correlation values
        for i in range(n_metrics):
            for j in range(n_metrics):
                text = ax.text(j, i, f'{corr_matrix[i, j]:.2f}', 
                              ha="center", va="center", color="black" if abs(corr_matrix[i, j]) < 0.5 else "white")
        
        ax.set_title(title)
        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def create_time_series_chart(data: List, metric: str, title: str = "") -> str:
        """Create time series chart as base64 image"""
        
        if not data:
            return ""
        
        # Extract time series data
        dates = [record.datetime for record in data]
        values = [record.value_1 for record in data]
        
        if not dates or not values:
            return ""
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(dates, values, linewidth=2, alpha=0.8)
        ax.scatter(dates, values, alpha=0.6, s=30)
        
        # Format
        ax.set_title(title or f"{metric.replace('_', ' ').title()} Over Time")
        ax.set_xlabel('Date')
        ax.set_ylabel(ChartGenerator._get_metric_unit(metric))
        ax.grid(True, alpha=0.3)
        
        # Format dates
        if len(dates) > 30:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def create_baseline_chart(baseline_data: Dict, metric: str) -> str:
        """Create baseline distribution chart"""
        
        if 'normal_range' not in baseline_data:
            return ""
        
        # Create distribution visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        
        mean_val = baseline_data['mean']
        std_val = baseline_data['std']
        lower = baseline_data['normal_range']['lower']
        upper = baseline_data['normal_range']['upper']
        
        # Create normal distribution for illustration
        x = np.linspace(mean_val - 3*std_val, mean_val + 3*std_val, 100)
        y = (1 / (std_val * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean_val) / std_val) ** 2)
        
        ax.fill_between(x, y, alpha=0.3, color='skyblue', label='Distribution')
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Average: {mean_val}')
        ax.axvspan(lower, upper, alpha=0.2, color='green', label=f'Normal Range: {lower}-{upper}')
        
        ax.set_title(f"{metric.replace('_', ' ').title()} Baseline Analysis")
        ax.set_xlabel(ChartGenerator._get_metric_unit(metric))
        ax.set_ylabel('Density')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def _get_metric_unit(metric: str) -> str:
        """Get unit for metric"""
        units = {
            'bp': 'mmHg',
            'hr': 'bpm',
            'steps': 'Steps',
            'sleep': 'Hours',
            'spo2': '%',
            'temp': '°F'
        }
        return units.get(metric, 'Value')


class ResearcherDashboard(BaseProcessor):
    """
    Generates researcher-focused HTML dashboard with technical analysis.
    """
    
    def process(self, data: Dict) -> str:
        """
        Generate researcher dashboard HTML.
        
        Parameters
        ----------
        data : Dict
            Combined analysis results
            
        Returns
        -------
        str
            HTML dashboard content
        """
        
        html = self._build_researcher_html(data)
        return html
    
    def _build_researcher_html(self, data: Dict) -> str:
        """Build complete researcher HTML dashboard"""
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GOQII Health Data - Research Analysis</title>
    <style>
        {self._get_research_css()}
    </style>
</head>
<body>
    <div class="container">
        <header class="dashboard-header">
            <div class="branding-top">By KCDH-A, Trivedi School of Biosciences Ashoka University</div>
            <h1>GOQII Health Data EDA - Research Analysis</h1>
            <p class="subtitle">Comprehensive Technical Analysis and Cohort Insights</p>
            <div class="meta-info">
                Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                Analysis Period: {self._get_date_range(data)}
            </div>
        </header>
        
        <div class="dashboard-grid">
            {self._build_cohort_summary(data)}
            {self._build_data_quality_section(data)}
            {self._build_correlation_analysis(data)}
            {self._build_anomaly_analysis(data)}
            {self._build_participant_overview(data)}
        </div>
        
        <footer class="dashboard-footer">
            <div class="branding-bottom">By KCDH-A, Trivedi School of Biosciences Ashoka University</div>
            <p>Generated by GOQII Health Data EDA Protocol | Research Analysis</p>
        </footer>
    </div>
</body>
</html>
"""
        return html
    
    def _build_cohort_summary(self, data: Dict) -> str:
        """Build cohort summary section"""
        
        technical_analysis = data.get('technical_analysis', {})
        cohort_stats = technical_analysis.get('cohort_analysis', {})
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">Cohort Summary</h2>'
        html += '<div class="stats-grid">'
        
        # Participant count
        participants = data.get('participant_insights', {})
        html += f'<div class="stat-card"><h3>{len(participants)}</h3><p>Total Participants</p></div>'
        
        # Data quality
        avg_quality = cohort_stats.get('average_data_quality', 0)
        html += f'<div class="stat-card"><h3>{avg_quality}%</h3><p>Average Data Quality</p></div>'
        
        # Compliance
        compliance = cohort_stats.get('average_compliance', 0)
        html += f'<div class="stat-card"><h3>{compliance}%</h3><p>Monitoring Compliance</p></div>'
        
        # Total records
        total_records = sum(
            sum(baseline.get('count', 0) for baseline in participant.get('health_baselines', {}).values())
            for participant in participants.values()
        )
        html += f'<div class="stat-card"><h3>{total_records:,}</h3><p>Total Data Points</p></div>'
        
        html += '</div>'
        
        # Add cohort correlations if available
        cohort_corr = cohort_stats.get('cohort_correlations', {})
        if cohort_corr:
            html += '<h3>Cohort-Level Correlations</h3>'
            html += '<div class="correlation-summary">'
            for corr_name, corr_data in cohort_corr.items():
                if corr_data.get('significant', False):
                    r_val = corr_data.get('r', 0)
                    confidence = corr_data.get('confidence', '')
                    html += f'<div class="correlation-item">'
                    html += f'<strong>{corr_name.replace("_vs_", " vs ")}</strong>: r={r_val:.3f} ({confidence})'
                    html += '</div>'
            html += '</div>'
        
        html += '</section>'
        return html
    
    def _build_data_quality_section(self, data: Dict) -> str:
        """Build data quality analysis section"""
        
        technical_analysis = data.get('technical_analysis', {})
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">Data Quality Analysis</h2>'
        
        # Missingness analysis
        missingness = technical_analysis.get('missingness_analysis', {})
        if missingness:
            html += '<h3>Data Completeness by Metric</h3>'
            html += '<div class="quality-grid">'
            
            for metric, miss_data in missingness.items():
                completeness = 100 - miss_data.get('missing_percentage', 0)
                quality_class = 'high' if completeness > 80 else 'medium' if completeness > 60 else 'low'
                html += f'<div class="quality-card {quality_class}">'
                html += f'<h4>{metric.replace("_", " ").title()}</h4>'
                html += f'<div class="quality-score">{completeness:.1f}%</div>'
                html += f'<p>Complete</p>'
                html += '</div>'
            html += '</div>'
        
        # Noise analysis
        noise_analysis = technical_analysis.get('noise_analysis', {})
        if noise_analysis:
            html += '<h3>Data Quality Flags</h3>'
            html += '<div class="noise-summary">'
            
            for metric, noise_data in noise_analysis.items():
                outlier_pct = noise_data.get('outlier_percentage', 0)
                quality_pct = noise_data.get('quality_percentage', 0)
                
                html += f'<div class="noise-item">'
                html += f'<strong>{metric.replace("_", " ").title()}</strong>: '
                html += f'{quality_pct:.1f}% clean data, {outlier_pct:.1f}% outliers'
                html += '</div>'
            html += '</div>'
        
        html += '</section>'
        return html
    
    def _build_correlation_analysis(self, data: Dict) -> str:
        """Build correlation analysis section"""
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">Correlation Analysis</h2>'
        
        # Get a representative participant's correlations for cohort-level insights
        participants = data.get('participant_insights', {})
        
        if participants:
            # Use first participant's correlation structure for display
            first_participant = next(iter(participants.values()))
            daily_correlations = first_participant.get('correlations', {}).get('daily', {})
            
            if daily_correlations:
                # Generate correlation heatmap
                chart_generator = ChartGenerator()
                heatmap_img = chart_generator.create_correlation_heatmap(
                    daily_correlations, 
                    "Average Daily Correlations Across Cohort"
                )
                
                if heatmap_img:
                    html += '<div class="chart-container">'
                    html += f'<img src="data:image/png;base64,{heatmap_img}" alt="Correlation Heatmap" class="chart-image">'
                    html += '</div>'
                
                # Strong correlations table
                html += '<h3>Significant Correlations</h3>'
                html += '<table class="correlation-table">'
                html += '<thead><tr><th>Metric Pair</th><th>Correlation</th><th>Confidence</th><th>Interpretation</th></tr></thead>'
                html += '<tbody>'
                
                for corr_name, corr_data in daily_correlations.items():
                    if corr_data.get('pearson', {}).get('significant', False):
                        r_val = corr_data['pearson']['r']
                        confidence = corr_data.get('confidence', 'uncertain')
                        interpretation = corr_data.get('interpretation', 'No interpretation available')
                        
                        html += '<tr>'
                        html += f'<td>{corr_name.replace("_vs_", " vs ").title()}</td>'
                        html += f'<td>{r_val:.3f}</td>'
                        html += f'<td>{confidence}</td>'
                        html += f'<td>{interpretation}</td>'
                        html += '</tr>'
                
                html += '</tbody></table>'
        
        html += '</section>'
        return html
    
    def _build_anomaly_analysis(self, data: Dict) -> str:
        """Build anomaly analysis section"""
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">Anomaly Detection</h2>'
        
        participants = data.get('participant_insights', {})
        
        if participants:
            # Aggregate anomaly statistics
            anomaly_stats = {}
            total_participants = len(participants)
            
            for participant_data in participants.values():
                anomalies = participant_data.get('anomalies', {})
                
                for metric, anomaly_data in anomalies.items():
                    if metric not in anomaly_stats:
                        anomaly_stats[metric] = {'count': 0, 'affected_participants': 0, 'total_anomalies': 0}
                    
                    anomaly_count = anomaly_data.get('anomaly_count', 0)
                    if anomaly_count > 0:
                        anomaly_stats[metric]['affected_participants'] += 1
                        anomaly_stats[metric]['total_anomalies'] += anomaly_count
            
            if anomaly_stats:
                html += '<div class="anomaly-grid">'
                
                for metric, stats in anomaly_stats.items():
                    affected_pct = (stats['affected_participants'] / total_participants) * 100
                    
                    html += f'<div class="anomaly-card">'
                    html += f'<h3>{metric.replace("_", " ").title()}</h3>'
                    html += f'<div class="anomaly-number">{stats["total_anomalies"]}</div>'
                    html += f'<p>Total Anomalies</p>'
                    html += f'<div class="anomaly-affected">{affected_pct:.1f}% participants affected</div>'
                    html += '</div>'
                
                html += '</div>'
        
        html += '</section>'
        return html
    
    def _build_participant_overview(self, data: Dict) -> str:
        """Build participant overview section"""
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">Participant Overview</h2>'
        
        participants = data.get('participant_insights', {})
        
        if participants:
            html += '<table class="participant-table">'
            html += '<thead><tr><th>Participant ID</th><th>Data Quality</th><th>Metrics Tracked</th><th>Key Findings</th></tr></thead>'
            html += '<tbody>'
            
            for participant_id, participant_data in participants.items():
                baselines = participant_data.get('health_baselines', {})
                insights = participant_data.get('personalized_insights', {})
                
                # Calculate data quality score
                total_records = sum(b.get('count', 0) for b in baselines.values())
                quality_score = min(100, (total_records / 100) * 100) if total_records > 0 else 0
                
                # Get key findings
                key_findings = insights.get('key_findings', [])
                findings_summary = '; '.join(key_findings[:2]) if key_findings else 'No significant findings'
                
                html += '<tr>'
                html += f'<td>{participant_id}</td>'
                html += f'<td>{quality_score:.0f}%</td>'
                html += f'<td>{len(baselines)} metrics</td>'
                html += f'<td>{findings_summary[:100]}{"..." if len(findings_summary) > 100 else ""}</td>'
                html += '</tr>'
            
            html += '</tbody></table>'
        
        html += '</section>'
        return html
    
    def _get_date_range(self, data: Dict) -> str:
        """Extract date range from data"""
        participants = data.get('participant_insights', {})
        
        if participants:
            first_participant = next(iter(participants.values()))
            data_period = first_participant.get('data_period', {})
            
            start_date = data_period.get('start_date', 'Unknown')
            end_date = data_period.get('end_date', 'Unknown')
            
            return f"{start_date} to {end_date}"
        
        return "Unknown"
    
    def _get_research_css(self) -> str:
        """Get CSS styles for researcher dashboard"""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        :root {
            --color-primary: #007AFF;
            --color-primary-light: #E3F2FD;
            --color-secondary: #5856D6;
            --color-success: #34C759;
            --color-warning: #FF9500;
            --color-error: #FF3B30;
            --color-gray-50: #FAFAFA;
            --color-gray-100: #F5F5F7;
            --color-gray-200: #E5E5EA;
            --color-gray-300: #D1D1D6;
            --color-gray-400: #8E8E93;
            --color-gray-600: #636366;
            --color-gray-800: #1C1C1E;
            --color-gray-900: #000000;
            --shadow-light: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            --shadow-medium: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.1);
            --shadow-heavy: 0 10px 25px rgba(0, 0, 0, 0.1), 0 4px 10px rgba(0, 0, 0, 0.06);
            --border-radius-sm: 8px;
            --border-radius-md: 12px;
            --border-radius-lg: 16px;
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            --spacing-2xl: 48px;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-feature-settings: 'kern' 1, 'liga' 1;
            line-height: 1.6;
            color: var(--color-gray-800);
            background: linear-gradient(135deg, var(--color-gray-50) 0%, var(--color-gray-100) 100%);
            font-weight: 400;
            letter-spacing: -0.01em;
        }
        
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: var(--spacing-xl); 
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, #FFFFFF 0%, var(--color-gray-50) 100%);
            color: var(--color-gray-800);
            padding: var(--spacing-2xl);
            border-radius: var(--spacing-lg);
            margin-bottom: var(--spacing-xl);
            text-align: center;
            box-shadow: var(--shadow-light);
            border: 1px solid var(--color-gray-200);
            position: relative;
            overflow: hidden;
        }
        
        .dashboard-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        }
        
        .branding-top {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--color-primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: var(--spacing-md);
            padding: var(--spacing-sm) var(--spacing-lg);
            background: var(--color-primary-light);
            border-radius: var(--border-radius-sm);
            display: inline-block;
        }
        
        .dashboard-header h1 { 
            font-size: 2.5rem; 
            font-weight: 700;
            margin-bottom: var(--spacing-md);
            color: var(--color-gray-900);
            letter-spacing: -0.025em;
        }
        
        .subtitle { 
            font-size: 1.125rem; 
            color: var(--color-gray-600);
            margin-bottom: var(--spacing-lg);
            font-weight: 400;
        }
        
        .meta-info { 
            font-size: 0.875rem; 
            color: var(--color-gray-400);
            font-weight: 500;
            line-height: 1.8;
        }
        
        .dashboard-grid { 
            display: grid; 
            gap: var(--spacing-xl);
        }
        
        .dashboard-section {
            background: #FFFFFF;
            padding: var(--spacing-xl);
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--color-gray-200);
            transition: box-shadow 0.3s ease;
        }
        
        .dashboard-section:hover {
            box-shadow: var(--shadow-heavy);
        }
        
        .section-title {
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: var(--spacing-lg);
            color: var(--color-gray-900);
            position: relative;
            padding-left: var(--spacing-lg);
        }
        
        .section-title::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            border-radius: 2px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: var(--spacing-lg);
            margin-bottom: var(--spacing-xl);
        }
        
        .stat-card {
            text-align: center;
            padding: var(--spacing-xl);
            background: linear-gradient(135deg, #FFFFFF 0%, var(--color-gray-50) 100%);
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow-light);
            border: 1px solid var(--color-gray-200);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }
        
        .stat-card h3 { 
            font-size: 2.75rem; 
            font-weight: 700;
            margin-bottom: var(--spacing-sm);
            color: var(--color-primary);
            letter-spacing: -0.02em;
        }
        
        .stat-card p { 
            font-size: 0.875rem; 
            color: var(--color-gray-600);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .quality-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-lg);
        }
        
        .quality-card {
            text-align: center;
            padding: var(--spacing-lg);
            border-radius: var(--border-radius-md);
            color: white;
            transition: transform 0.2s ease;
        }
        
        .quality-card:hover {
            transform: scale(1.02);
        }
        
        .quality-card.high { background: linear-gradient(135deg, var(--color-success) 0%, #28A745 100%); }
        .quality-card.medium { background: linear-gradient(135deg, var(--color-warning) 0%, #FD7E14 100%); }
        .quality-card.low { background: linear-gradient(135deg, var(--color-error) 0%, #DC3545 100%); }
        
        .quality-score { 
            font-size: 2rem; 
            font-weight: 700;
            margin-bottom: var(--spacing-xs);
        }
        
        .chart-container {
            text-align: center;
            margin: var(--spacing-xl) 0;
            padding: var(--spacing-lg);
            background: var(--color-gray-50);
            border-radius: var(--border-radius-md);
        }
        
        .chart-image {
            max-width: 100%;
            height: auto;
            border-radius: var(--border-radius-sm);
            box-shadow: var(--shadow-light);
        }
        
        .correlation-table, .participant-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: var(--spacing-lg);
            font-size: 0.875rem;
        }
        
        .correlation-table th, .correlation-table td,
        .participant-table th, .participant-table td {
            padding: var(--spacing-md);
            text-align: left;
            border-bottom: 1px solid var(--color-gray-200);
        }
        
        .correlation-table th, .participant-table th {
            background-color: var(--color-gray-100);
            font-weight: 600;
            color: var(--color-gray-800);
            text-transform: uppercase;
            letter-spacing: 0.025em;
            font-size: 0.75rem;
        }
        
        .correlation-table tr:hover, .participant-table tr:hover {
            background-color: var(--color-gray-50);
        }
        
        .anomaly-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: var(--spacing-lg);
        }
        
        .anomaly-card {
            text-align: center;
            padding: var(--spacing-xl);
            background: linear-gradient(135deg, #FFFFFF 0%, var(--color-primary-light) 100%);
            border-radius: var(--border-radius-lg);
            border: 1px solid var(--color-primary);
            border-width: 0 0 0 4px;
            transition: all 0.3s ease;
        }
        
        .anomaly-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }
        
        .anomaly-number { 
            font-size: 2.75rem; 
            font-weight: 700; 
            color: var(--color-primary);
            margin-bottom: var(--spacing-sm);
        }
        
        .anomaly-affected { 
            font-size: 0.875rem; 
            color: var(--color-gray-600);
            margin-top: var(--spacing-sm);
            font-weight: 500;
        }
        
        .correlation-summary, .noise-summary {
            display: grid;
            gap: var(--spacing-md);
            margin-top: var(--spacing-lg);
        }
        
        .correlation-item, .noise-item {
            padding: var(--spacing-lg);
            background: var(--color-gray-50);
            border-radius: var(--border-radius-md);
            border-left: 4px solid var(--color-primary);
            transition: all 0.2s ease;
        }
        
        .correlation-item:hover, .noise-item:hover {
            background: var(--color-primary-light);
            transform: translateX(4px);
        }
        
        .dashboard-footer {
            text-align: center;
            margin-top: var(--spacing-2xl);
            padding: var(--spacing-xl);
            color: var(--color-gray-600);
            font-size: 0.875rem;
            background: #FFFFFF;
            border-radius: var(--border-radius-lg);
            border: 1px solid var(--color-gray-200);
        }
        
        .branding-bottom {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--color-primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: var(--spacing-sm);
        }
        
        @media (max-width: 768px) {
            .container { padding: var(--spacing-lg); }
            .dashboard-header { padding: var(--spacing-lg); }
            .dashboard-header h1 { font-size: 2rem; }
            .stats-grid { grid-template-columns: 1fr 1fr; gap: var(--spacing-md); }
            .quality-grid { grid-template-columns: 1fr 1fr; }
            .anomaly-grid { grid-template-columns: 1fr; }
        }
        """


class ParticipantDashboard(BaseProcessor):
    """
    Generates participant-focused HTML dashboard with personalized insights.
    """
    
    def process(self, data: Dict) -> str:
        """
        Generate participant dashboard HTML.
        
        Parameters
        ----------
        data : Dict
            Single participant insights
            
        Returns
        -------
        str
            HTML dashboard content
        """
        
        html = self._build_participant_html(data)
        return html
    
    def _build_participant_html(self, data: Dict) -> str:
        """Build complete participant HTML dashboard"""
        
        participant_id = data.get('participant_id', 'Unknown')
        insights = data.get('personalized_insights', {})
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Health Insights - {participant_id}</title>
    <style>
        {self._get_participant_css()}
    </style>
</head>
<body>
    <div class="container">
        <header class="dashboard-header">
            <div class="branding-top">By KCDH-A, Trivedi School of Biosciences Ashoka University</div>
            <h1>Your Personal Health Insights</h1>
            <p class="subtitle">Data-driven insights from your health monitoring</p>
            <div class="patient-id">Patient ID: {participant_id.replace('participant-', '').upper()}</div>
        </header>
        
        <div class="dashboard-grid">
            {self._build_health_summary(data)}
            {self._build_key_findings(data)}
            {self._build_baseline_analysis(data)}
            {self._build_health_connections(data)}
            {self._build_behavioral_insights(data)}
            {self._build_recommendations(data)}
        </div>
        
        <footer class="dashboard-footer">
            <div class="branding-bottom">By KCDH-A, Trivedi School of Biosciences Ashoka University</div>
            <p>Generated on: {datetime.now().strftime('%B %d, %Y')}</p>
            <p>This report is for informational purposes only. Please consult your healthcare provider for medical advice.</p>
        </footer>
    </div>
</body>
</html>
"""
        return html
    
    def _build_health_summary(self, data: Dict) -> str:
        """Build health summary section"""
        
        insights = data.get('personalized_insights', {})
        summary = insights.get('health_summary', {})
        
        html = '<section class="dashboard-section summary-section">'
        html += '<h2 class="section-title">📊 Your Health Summary</h2>'
        
        # Data quality score
        quality_score = summary.get('data_quality_score', 0)
        score_class = 'high' if quality_score > 80 else 'medium' if quality_score > 60 else 'low'
        html += f'<div class="quality-indicator">'
        html += f'<h3>Data Quality Score</h3>'
        html += f'<div class="score-circle {score_class}">'
        html += f'<span>{quality_score}%</span>'
        html += '</div>'
        html += '</div>'
        
        # Health metrics
        metrics = summary.get('health_metrics', [])
        if metrics:
            html += '<div class="metrics-summary">'
            html += '<h3>Your Average Health Metrics</h3>'
            html += '<div class="metrics-grid">'
            
            for metric in metrics:
                html += f'<div class="metric-item">📈 {metric}</div>'
            
            html += '</div>'
            html += '</div>'
        
        # Monitoring period
        period = summary.get('monitoring_period', {})
        if period:
            start_date = period.get('start_date', '')
            end_date = period.get('end_date', '')
            if start_date and end_date:
                html += f'<div class="period-info">'
                html += f'<p><strong>Monitoring Period:</strong> {start_date} to {end_date}</p>'
                html += '</div>'
        
        html += '</section>'
        return html
    
    def _build_key_findings(self, data: Dict) -> str:
        """Build key findings section"""
        
        insights = data.get('personalized_insights', {})
        findings = insights.get('key_findings', [])
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">🔍 Key Health Findings</h2>'
        
        if findings:
            html += '<div class="findings-list">'
            
            for i, finding in enumerate(findings):
                icon = "⚠️" if any(word in finding.lower() for word in ['elevated', 'high', 'low', 'below', 'above']) else "ℹ️"
                html += f'<div class="finding-item">'
                html += f'<span class="finding-icon">{icon}</span>'
                html += f'<span class="finding-text">{finding}</span>'
                html += '</div>'
            
            html += '</div>'
        else:
            html += '<p class="no-data">No significant findings identified in your health data.</p>'
        
        html += '</section>'
        return html
    
    def _build_baseline_analysis(self, data: Dict) -> str:
        """Build baseline analysis with charts"""
        
        baselines = data.get('health_baselines', {})
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">📈 Your Health Baselines</h2>'
        
        if baselines:
            html += '<div class="baseline-grid">'
            
            for metric, baseline in baselines.items():
                mean_val = baseline.get('mean', 0)
                interpretation = baseline.get('interpretation', '')
                normal_range = baseline.get('normal_range', {})
                
                # Generate baseline chart
                chart_generator = ChartGenerator()
                chart_img = chart_generator.create_baseline_chart(baseline, metric)
                
                html += f'<div class="baseline-card">'
                html += f'<h3>{metric.replace("_", " ").title()}</h3>'
                html += f'<div class="baseline-value">{mean_val} {ChartGenerator._get_metric_unit(metric)}</div>'
                html += f'<p class="baseline-interpretation">{interpretation}</p>'
                
                if normal_range:
                    html += f'<div class="normal-range">'
                    html += f'Your normal range: {normal_range.get("lower", "N/A")} - {normal_range.get("upper", "N/A")}'
                    html += '</div>'
                
                if chart_img:
                    html += f'<div class="baseline-chart">'
                    html += f'<img src="data:image/png;base64,{chart_img}" alt="{metric} baseline chart">'
                    html += '</div>'
                
                html += '</div>'
            
            html += '</div>'
        else:
            html += '<p class="no-data">No baseline data available.</p>'
        
        html += '</section>'
        return html
    
    def _build_health_connections(self, data: Dict) -> str:
        """Build user-friendly correlation analysis section"""
        
        correlations = data.get('correlations', {}).get('daily', {})
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">🔗 Your Health Connections</h2>'
        html += '<p class="section-description">Understanding how your health metrics influence each other can help you make better lifestyle choices.</p>'
        
        if correlations:
            # Separate correlations by strength (regardless of statistical significance)
            strong_positive = []
            strong_negative = []
            moderate_correlations = []
            weak_correlations = []
            
            for corr_name, corr_data in correlations.items():
                pearson_data = corr_data.get('pearson', {})
                r_value = pearson_data.get('r', 0)
                n_days = corr_data.get('n_days', 0)
                
                # Only show correlations with reasonable sample size
                if n_days >= 3:
                    interpretation = corr_data.get('interpretation', '')
                    
                    # Clean up correlation name for display
                    metric_pair = corr_name.replace('_vs_', ' and ').replace('_', ' ').title()
                    
                    correlation_info = {
                        'pair': metric_pair,
                        'strength': abs(r_value),
                        'direction': 'positive' if r_value > 0 else 'negative',
                        'r_value': r_value,
                        'interpretation': interpretation,
                        'confidence': corr_data.get('confidence', 'uncertain'),
                        'n_days': n_days,
                        'significant': pearson_data.get('significant', 'False') == 'True'
                    }
                    
                    # Categorize by strength
                    if abs(r_value) >= 0.6:  # Lowered threshold for personal insights
                        if r_value > 0:
                            strong_positive.append(correlation_info)
                        else:
                            strong_negative.append(correlation_info)
                    elif abs(r_value) >= 0.3:  # Lowered threshold for moderate
                        moderate_correlations.append(correlation_info)
                    elif abs(r_value) >= 0.1:  # Show even weak patterns
                        weak_correlations.append(correlation_info)
            
            # Display strong positive correlations
            if strong_positive:
                html += '<div class="correlation-category">'
                html += '<h3 class="correlation-category-title">💪 Strong Positive Patterns</h3>'
                html += '<p class="category-description">When one goes up, the other tends to go up too</p>'
                html += '<div class="correlation-cards">'
                
                for corr in strong_positive:
                    confidence_badge = self._get_confidence_badge(corr)
                    html += f'<div class="correlation-card positive">'
                    html += f'<div class="correlation-icon">📈</div>'
                    html += f'<h4>{corr["pair"]}</h4>'
                    html += f'<div class="correlation-strength">Pattern Strength: {corr["strength"]:.2f} {confidence_badge}</div>'
                    html += f'<div class="sample-info">Based on {corr["n_days"]} days of data</div>'
                    html += f'<p class="correlation-explanation">{self._get_user_friendly_explanation(corr)}</p>'
                    html += '</div>'
                
                html += '</div></div>'
            
            # Display strong negative correlations
            if strong_negative:
                html += '<div class="correlation-category">'
                html += '<h3 class="correlation-category-title">🔄 Strong Inverse Patterns</h3>'
                html += '<p class="category-description">When one goes up, the other tends to go down</p>'
                html += '<div class="correlation-cards">'
                
                for corr in strong_negative:
                    confidence_badge = self._get_confidence_badge(corr)
                    html += f'<div class="correlation-card negative">'
                    html += f'<div class="correlation-icon">📉</div>'
                    html += f'<h4>{corr["pair"]}</h4>'
                    html += f'<div class="correlation-strength">Pattern Strength: {corr["strength"]:.2f} {confidence_badge}</div>'
                    html += f'<div class="sample-info">Based on {corr["n_days"]} days of data</div>'
                    html += f'<p class="correlation-explanation">{self._get_user_friendly_explanation(corr)}</p>'
                    html += '</div>'
                
                html += '</div></div>'
            
            # Display moderate correlations
            if moderate_correlations:
                html += '<div class="correlation-category">'
                html += '<h3 class="correlation-category-title">🔍 Moderate Patterns</h3>'
                html += '<p class="category-description">Noticeable relationships worth monitoring</p>'
                html += '<div class="correlation-cards">'
                
                for corr in moderate_correlations:
                    direction_icon = "📊" if corr["direction"] == "positive" else "📉"
                    confidence_badge = self._get_confidence_badge(corr)
                    html += f'<div class="correlation-card moderate">'
                    html += f'<div class="correlation-icon">{direction_icon}</div>'
                    html += f'<h4>{corr["pair"]}</h4>'
                    html += f'<div class="correlation-strength">Pattern Strength: {corr["strength"]:.2f} {confidence_badge}</div>'
                    html += f'<div class="sample-info">Based on {corr["n_days"]} days of data</div>'
                    html += f'<p class="correlation-explanation">{self._get_user_friendly_explanation(corr)}</p>'
                    html += '</div>'
                
                html += '</div></div>'
            
            # Display weak correlations only if no strong/moderate ones exist
            if not (strong_positive or strong_negative or moderate_correlations) and weak_correlations:
                html += '<div class="correlation-category">'
                html += '<h3 class="correlation-category-title">� Emerging Patterns</h3>'
                html += '<p class="category-description">Early patterns that may become clearer with more data</p>'
                html += '<div class="correlation-cards">'
                
                # Show only top 3 weak correlations
                for corr in sorted(weak_correlations, key=lambda x: x['strength'], reverse=True)[:3]:
                    direction_icon = "📈" if corr["direction"] == "positive" else "📉"
                    confidence_badge = self._get_confidence_badge(corr)
                    html += f'<div class="correlation-card weak">'
                    html += f'<div class="correlation-icon">{direction_icon}</div>'
                    html += f'<h4>{corr["pair"]}</h4>'
                    html += f'<div class="correlation-strength">Pattern Strength: {corr["strength"]:.2f} {confidence_badge}</div>'
                    html += f'<div class="sample-info">Based on {corr["n_days"]} days of data</div>'
                    html += f'<p class="correlation-explanation">A subtle pattern that might strengthen as we collect more data.</p>'
                    html += '</div>'
                
                html += '</div></div>'
            
            # Add actionable insights section if we have any correlations
            if strong_positive or strong_negative or moderate_correlations or weak_correlations:
                html += '<div class="correlation-insights">'
                html += '<h3>💡 What This Means for You</h3>'
                html += '<div class="insight-tips">'
                
                html += '<div class="tip-card">'
                html += '<div class="tip-icon">📊</div>'
                html += '<p><strong>Personal Patterns:</strong> These patterns are specific to your body and lifestyle. Use them to optimize your health routines.</p>'
                html += '</div>'
                
                html += '<div class="tip-card">'
                html += '<div class="tip-icon">⏰</div>'
                html += '<p><strong>More Data = Better Insights:</strong> Patterns become more reliable as we collect more of your health data over time.</p>'
                html += '</div>'
                
                if strong_positive or moderate_correlations:
                    html += '<div class="tip-card">'
                    html += '<div class="tip-icon">🎯</div>'
                    html += '<p><strong>Focus Areas:</strong> Consider focusing on the strongest patterns to get the most impact from lifestyle changes.</p>'
                    html += '</div>'
                
                html += '</div></div>'
            else:
                html += '<div class="no-correlations">'
                html += '<div class="no-corr-icon">🔍</div>'
                html += '<h3>Independent Health Metrics</h3>'
                html += '<p>Your health metrics show independent patterns currently. This gives you targeted control over different aspects of your health. As we collect more data, clearer patterns may emerge.</p>'
                html += '</div>'
        
        else:
            html += '<div class="no-correlations">'
            html += '<div class="no-corr-icon">📊</div>'
            html += '<h3>Building Your Health Profile</h3>'
            html += '<p>As we collect more of your health data, we\'ll be able to identify meaningful connections between your various health metrics.</p>'
            html += '</div>'
        
        html += '</section>'
        return html
    
    def _get_confidence_badge(self, correlation_info: Dict) -> str:
        """Generate confidence badge for correlation"""
        confidence = correlation_info.get('confidence', 'uncertain')
        significant = correlation_info.get('significant', False)
        
        if significant:
            return '<span class="confidence-badge high">✓ Statistically Strong</span>'
        elif confidence == 'pretty sure':
            return '<span class="confidence-badge medium">~ Likely Pattern</span>'
        else:
            return '<span class="confidence-badge low">? Emerging Pattern</span>'
    
    def _get_user_friendly_explanation(self, correlation_info: Dict) -> str:
        """Generate user-friendly explanation for correlations"""
        
        pair = correlation_info['pair'].lower()
        direction = correlation_info['direction']
        strength = correlation_info['strength']
        
        # Create contextual explanations based on metric combinations
        explanations = {
            'positive': {
                'high': "These metrics move together consistently. Improving one typically helps the other.",
                'medium': "These metrics often influence each other, though other factors play a role too."
            },
            'negative': {
                'high': "These metrics balance each other - when one increases, the other naturally decreases.",
                'medium': "These metrics sometimes work in opposite directions, reflecting your body's balancing systems."
            }
        }
        
        strength_category = 'high' if strength >= 0.7 else 'medium'
        
        base_explanation = explanations[direction][strength_category]
        
        # Add specific insights for common metric pairs
        if 'sleep' in pair and 'heart rate' in pair:
            if direction == 'negative':
                base_explanation += " Better sleep quality often leads to a more relaxed heart rate."
        elif 'steps' in pair and 'heart rate' in pair:
            if direction == 'positive':
                base_explanation += " More physical activity typically increases your heart rate during active periods."
        elif 'blood pressure' in pair and 'heart rate' in pair:
            if direction == 'positive':
                base_explanation += " These cardiovascular metrics often respond similarly to stress and activity."
        
        return base_explanation

    def _build_behavioral_insights(self, data: Dict) -> str:
        """Build behavioral insights section"""
        
        insights = data.get('personalized_insights', {})
        behavioral = insights.get('behavioral_insights', [])
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">🎯 Your Health Patterns</h2>'
        
        if behavioral:
            html += '<div class="behavioral-insights">'
            
            for insight in behavioral:
                html += f'<div class="insight-item">'
                html += f'<span class="insight-icon">💡</span>'
                html += f'<span class="insight-text">{insight}</span>'
                html += '</div>'
            
            html += '</div>'
        else:
            html += '<p class="no-data">No specific behavioral patterns identified.</p>'
        
        html += '</section>'
        return html
    
    def _build_recommendations(self, data: Dict) -> str:
        """Build recommendations section"""
        
        insights = data.get('personalized_insights', {})
        recommendations = insights.get('recommendations', [])
        
        html = '<section class="dashboard-section">'
        html += '<h2 class="section-title">💪 Your Personalized Recommendations</h2>'
        
        if recommendations:
            # Group by priority
            high_priority = [r for r in recommendations if r.get('priority') == 'High']
            medium_priority = [r for r in recommendations if r.get('priority') == 'Medium']
            low_priority = [r for r in recommendations if r.get('priority') == 'Low']
            
            for priority_group, title, color in [
                (high_priority, "🚨 High Priority", "high"),
                (medium_priority, "⚡ Medium Priority", "medium"),
                (low_priority, "💡 Low Priority", "low")
            ]:
                if priority_group:
                    html += f'<h3>{title}</h3>'
                    html += '<div class="recommendations-list">'
                    
                    for rec in priority_group:
                        html += f'<div class="recommendation-card {color}">'
                        html += f'<h4>{rec.get("category", "General")}</h4>'
                        html += f'<p class="rec-text">{rec.get("recommendation", "")}</p>'
                        
                        # Action items
                        actions = rec.get('action_items', [])
                        if actions:
                            html += '<ul class="action-list">'
                            for action in actions:
                                html += f'<li>{action}</li>'
                            html += '</ul>'
                        
                        # Target
                        target = rec.get('target', '')
                        if target:
                            html += f'<div class="target">🎯 Target: {target}</div>'
                        
                        html += '</div>'
                    
                    html += '</div>'
        else:
            html += '<p class="no-data">No specific recommendations at this time. Keep up the good work!</p>'
        
        html += '</section>'
        return html
    
    def _get_participant_css(self) -> str:
        """Get CSS styles for participant dashboard"""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        :root {
            --color-primary: #007AFF;
            --color-primary-light: #E3F2FD;
            --color-secondary: #5856D6;
            --color-success: #34C759;
            --color-warning: #FF9500;
            --color-error: #FF3B30;
            --color-gray-50: #FAFAFA;
            --color-gray-100: #F5F5F7;
            --color-gray-200: #E5E5EA;
            --color-gray-300: #D1D1D6;
            --color-gray-400: #8E8E93;
            --color-gray-600: #636366;
            --color-gray-800: #1C1C1E;
            --color-gray-900: #000000;
            --shadow-light: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            --shadow-medium: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.1);
            --shadow-heavy: 0 10px 25px rgba(0, 0, 0, 0.1), 0 4px 10px rgba(0, 0, 0, 0.06);
            --border-radius-sm: 8px;
            --border-radius-md: 12px;
            --border-radius-lg: 16px;
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            --spacing-2xl: 48px;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-feature-settings: 'kern' 1, 'liga' 1;
            line-height: 1.6;
            color: var(--color-gray-800);
            background: linear-gradient(135deg, var(--color-gray-50) 0%, var(--color-primary-light) 100%);
            min-height: 100vh;
            font-weight: 400;
            letter-spacing: -0.01em;
        }
        
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: var(--spacing-xl); 
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, #FFFFFF 0%, var(--color-gray-50) 100%);
            color: var(--color-gray-800);
            padding: var(--spacing-2xl);
            border-radius: var(--border-radius-lg);
            margin-bottom: var(--spacing-xl);
            text-align: center;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--color-gray-200);
            position: relative;
            overflow: hidden;
        }
        
        .dashboard-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        }
        
        .branding-top {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--color-primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: var(--spacing-md);
            padding: var(--spacing-sm) var(--spacing-lg);
            background: var(--color-primary-light);
            border-radius: var(--border-radius-sm);
            display: inline-block;
        }
        
        .dashboard-header h1 { 
            font-size: 2.5rem; 
            font-weight: 700;
            margin-bottom: var(--spacing-md);
            color: var(--color-gray-900);
            letter-spacing: -0.025em;
        }
        
        .subtitle { 
            font-size: 1.125rem; 
            color: var(--color-gray-600);
            margin-bottom: var(--spacing-lg);
            font-weight: 400;
        }
        
        .patient-id { 
            font-size: 1rem; 
            color: var(--color-primary);
            font-weight: 600;
            padding: var(--spacing-sm) var(--spacing-lg);
            background: var(--color-primary-light);
            border-radius: var(--border-radius-sm);
            display: inline-block;
        }
        
        .dashboard-grid { 
            display: grid; 
            gap: var(--spacing-xl);
        }
        
        .dashboard-section {
            background: rgba(255, 255, 255, 0.95);
            padding: var(--spacing-xl);
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow-medium);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
        }
        
        .dashboard-section:hover {
            box-shadow: var(--shadow-heavy);
            transform: translateY(-2px);
        }
        
        .section-title {
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: var(--spacing-lg);
            color: var(--color-gray-900);
            position: relative;
            padding-left: var(--spacing-lg);
        }
        
        .section-title::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            border-radius: 2px;
        }
        
        .summary-section {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            color: white;
            border: none;
        }
        
        .summary-section .section-title { 
            color: white; 
            padding-left: var(--spacing-lg);
        }
        
        .summary-section .section-title::before {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .quality-indicator {
            text-align: center;
            margin-bottom: var(--spacing-xl);
        }
        
        .score-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: var(--spacing-lg) auto;
            font-size: 1.5rem;
            font-weight: 700;
            box-shadow: var(--shadow-medium);
            border: 4px solid rgba(255, 255, 255, 0.2);
        }
        
        .score-circle.high { background: var(--color-success); }
        .score-circle.medium { background: var(--color-warning); }
        .score-circle.low { background: var(--color-error); }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: var(--spacing-md);
            margin-top: var(--spacing-lg);
        }
        
        .metric-item {
            padding: var(--spacing-lg);
            background: rgba(255, 255, 255, 0.2);
            border-radius: var(--border-radius-md);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-weight: 500;
        }
        
        .findings-list, .behavioral-insights {
            display: grid;
            gap: var(--spacing-md);
        }
        
        .finding-item, .insight-item {
            display: flex;
            align-items: flex-start;
            gap: var(--spacing-lg);
            padding: var(--spacing-lg);
            background: var(--color-gray-50);
            border-radius: var(--border-radius-md);
            border-left: 4px solid var(--color-primary);
            transition: all 0.3s ease;
        }
        
        .finding-item:hover, .insight-item:hover {
            background: var(--color-primary-light);
            transform: translateX(4px);
            box-shadow: var(--shadow-light);
        }
        
        .finding-icon, .insight-icon {
            font-size: 1.2rem;
            flex-shrink: 0;
            margin-top: var(--spacing-xs);
        }
        
        .baseline-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: var(--spacing-xl);
        }
        
        .baseline-card {
            padding: var(--spacing-xl);
            background: var(--color-gray-50);
            border-radius: var(--border-radius-lg);
            text-align: center;
            border: 2px solid var(--color-gray-200);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .baseline-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        }
        
        .baseline-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-heavy);
            border-color: var(--color-primary);
        }
        
        .baseline-card h3 {
            color: var(--color-gray-900);
            margin-bottom: var(--spacing-lg);
            font-weight: 600;
        }
        
        .baseline-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--color-primary);
            margin-bottom: var(--spacing-lg);
            letter-spacing: -0.02em;
        }
        
        .baseline-interpretation {
            color: var(--color-gray-600);
            margin-bottom: var(--spacing-lg);
            font-weight: 500;
            line-height: 1.5;
        }
        
        .normal-range {
            font-size: 0.875rem;
            color: var(--color-success);
            font-weight: 600;
            margin-bottom: var(--spacing-lg);
            padding: var(--spacing-sm) var(--spacing-md);
            background: rgba(52, 199, 89, 0.1);
            border-radius: var(--border-radius-sm);
            display: inline-block;
        }
        
        .baseline-chart img {
            max-width: 100%;
            height: auto;
            border-radius: var(--border-radius-sm);
            box-shadow: var(--shadow-light);
        }
        
        .recommendations-list {
            display: grid;
            gap: var(--spacing-lg);
            margin-bottom: var(--spacing-xl);
        }
        
        .recommendation-card {
            padding: var(--spacing-xl);
            border-radius: var(--border-radius-lg);
            border-left: 5px solid;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .recommendation-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            opacity: 0.3;
        }
        
        .recommendation-card.high {
            background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
            border-left-color: var(--color-error);
        }
        
        .recommendation-card.high::before {
            background: var(--color-error);
        }
        
        .recommendation-card.medium {
            background: linear-gradient(135deg, #FFFBEB 0%, #FED7AA 100%);
            border-left-color: var(--color-warning);
        }
        
        .recommendation-card.medium::before {
            background: var(--color-warning);
        }
        
        .recommendation-card.low {
            background: linear-gradient(135deg, #F0F9FF 0%, #DBEAFE 100%);
            border-left-color: var(--color-primary);
        }
        
        .recommendation-card.low::before {
            background: var(--color-primary);
        }
        
        .recommendation-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }
        
        .recommendation-card h4 {
            color: var(--color-gray-900);
            margin-bottom: var(--spacing-md);
            font-weight: 600;
        }
        
        .rec-text {
            margin-bottom: var(--spacing-lg);
            font-weight: 500;
            color: var(--color-gray-800);
            line-height: 1.6;
        }
        
        .action-list {
            margin: var(--spacing-lg) 0;
            padding-left: var(--spacing-lg);
        }
        
        .action-list li {
            margin-bottom: var(--spacing-sm);
            color: var(--color-gray-700);
            line-height: 1.5;
        }
        
        .target {
            margin-top: var(--spacing-lg);
            padding: var(--spacing-md);
            background: rgba(0,0,0,0.05);
            border-radius: var(--border-radius-sm);
            font-weight: 600;
            color: var(--color-gray-800);
        }
        
        .no-data {
            text-align: center;
            color: var(--color-gray-400);
            font-style: italic;
            padding: var(--spacing-2xl);
            font-size: 1.125rem;
        }
        
        .dashboard-footer {
            text-align: center;
            margin-top: var(--spacing-2xl);
            padding: var(--spacing-xl);
            background: rgba(255, 255, 255, 0.95);
            border-radius: var(--border-radius-lg);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: var(--color-gray-600);
            font-size: 0.875rem;
        }
        
        .branding-bottom {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--color-primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: var(--spacing-sm);
        }
        
        .period-info {
            margin-top: var(--spacing-lg);
            padding: var(--spacing-lg);
            background: rgba(255, 255, 255, 0.2);
            border-radius: var(--border-radius-md);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Health Connections/Correlation Styles */
        .section-description {
            font-size: 1rem;
            color: var(--color-gray-600);
            margin-bottom: var(--spacing-xl);
            line-height: 1.6;
        }
        
        .correlation-category {
            margin-bottom: var(--spacing-2xl);
        }
        
        .correlation-category-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--color-gray-900);
            margin-bottom: var(--spacing-sm);
        }
        
        .category-description {
            font-size: 0.875rem;
            color: var(--color-gray-500);
            margin-bottom: var(--spacing-lg);
            font-style: italic;
        }
        
        .correlation-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: var(--spacing-lg);
            margin-bottom: var(--spacing-xl);
        }
        
        .correlation-card {
            padding: var(--spacing-lg);
            border-radius: var(--border-radius-lg);
            border: 2px solid;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .correlation-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
        }
        
        .correlation-card.positive {
            background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
            border-color: var(--color-success);
        }
        
        .correlation-card.positive::before {
            background: var(--color-success);
        }
        
        .correlation-card.negative {
            background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
            border-color: var(--color-error);
        }
        
        .correlation-card.negative::before {
            background: var(--color-error);
        }
        
        .correlation-card.moderate {
            background: linear-gradient(135deg, #FFFBEB 0%, #FED7AA 100%);
            border-color: var(--color-warning);
        }
        
        .correlation-card.moderate::before {
            background: var(--color-warning);
        }
        
        .correlation-card.weak {
            background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
            border-color: var(--color-gray-400);
        }
        
        .correlation-card.weak::before {
            background: var(--color-gray-400);
        }
        
        .correlation-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-heavy);
        }
        
        .correlation-icon {
            font-size: 2rem;
            margin-bottom: var(--spacing-md);
            text-align: center;
        }
        
        .correlation-card h4 {
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--color-gray-900);
            margin-bottom: var(--spacing-sm);
            text-align: center;
        }
        
        .correlation-strength {
            font-size: 0.875rem;
            font-weight: 600;
            text-align: center;
            margin-bottom: var(--spacing-sm);
            padding: var(--spacing-xs) var(--spacing-sm);
            border-radius: var(--border-radius-sm);
            background: rgba(0, 0, 0, 0.05);
        }
        
        .sample-info {
            font-size: 0.75rem;
            color: var(--color-gray-500);
            text-align: center;
            margin-bottom: var(--spacing-md);
            font-style: italic;
        }
        
        .confidence-badge {
            display: inline-block;
            font-size: 0.65rem;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: var(--spacing-xs);
            font-weight: 500;
        }
        
        .confidence-badge.high {
            background: var(--color-success);
            color: white;
        }
        
        .confidence-badge.medium {
            background: var(--color-warning);
            color: white;
        }
        
        .confidence-badge.low {
            background: var(--color-gray-400);
            color: white;
        }
        
        .correlation-explanation {
            font-size: 0.875rem;
            color: var(--color-gray-700);
            line-height: 1.5;
            text-align: center;
        }
        
        .correlation-insights {
            margin-top: var(--spacing-2xl);
            padding: var(--spacing-xl);
            background: linear-gradient(135deg, var(--color-primary-light) 0%, rgba(0, 122, 255, 0.05) 100%);
            border-radius: var(--border-radius-lg);
            border: 1px solid rgba(0, 122, 255, 0.2);
        }
        
        .correlation-insights h3 {
            color: var(--color-gray-900);
            margin-bottom: var(--spacing-lg);
            text-align: center;
        }
        
        .insight-tips {
            display: grid;
            gap: var(--spacing-md);
        }
        
        .tip-card {
            display: flex;
            align-items: flex-start;
            gap: var(--spacing-md);
            padding: var(--spacing-lg);
            background: rgba(255, 255, 255, 0.7);
            border-radius: var(--border-radius-md);
            backdrop-filter: blur(10px);
        }
        
        .tip-icon {
            font-size: 1.5rem;
            flex-shrink: 0;
            margin-top: var(--spacing-xs);
        }
        
        .tip-card p {
            color: var(--color-gray-800);
            line-height: 1.5;
            margin: 0;
        }
        
        .no-correlations {
            text-align: center;
            padding: var(--spacing-2xl);
            background: linear-gradient(135deg, var(--color-gray-50) 0%, var(--color-gray-100) 100%);
            border-radius: var(--border-radius-lg);
            border: 2px dashed var(--color-gray-300);
        }
        
        .no-corr-icon {
            font-size: 3rem;
            margin-bottom: var(--spacing-lg);
        }
        
        .no-correlations h3 {
            color: var(--color-gray-800);
            margin-bottom: var(--spacing-md);
        }
        
        .no-correlations p {
            color: var(--color-gray-600);
            line-height: 1.6;
            max-width: 500px;
            margin: 0 auto;
        }
        
        @media (max-width: 768px) {
            .container { padding: var(--spacing-lg); }
            .dashboard-header { padding: var(--spacing-lg); }
            .dashboard-header h1 { font-size: 2rem; }
            .baseline-grid { grid-template-columns: 1fr; }
            .metrics-grid { grid-template-columns: 1fr; }
            .section-title { font-size: 1.5rem; }
            .correlation-cards { grid-template-columns: 1fr; }
        }
        """


class DashboardGenerator(BaseProcessor):
    """
    Main dashboard generator coordinating researcher and participant views.
    """
    
    def process(self, data: Dict) -> Dict[str, str]:
        """
        Generate both researcher and participant dashboards.
        
        Parameters
        ----------
        data : Dict
            Complete analysis results
            
        Returns
        -------
        Dict[str, str]
            Generated HTML dashboards {'researcher': html, 'participants': {id: html}}
        """
        
        self.logger.info("Generating HTML dashboards")
        
        # Generate researcher dashboard
        researcher_dashboard = ResearcherDashboard()
        researcher_html = researcher_dashboard.process(data)
        
        # Generate participant dashboards
        participant_dashboard = ParticipantDashboard()
        participant_htmls = {}
        
        participants = data.get('participant_insights', {})
        for participant_id, participant_data in participants.items():
            participant_html = participant_dashboard.process(participant_data)
            participant_htmls[participant_id] = participant_html
        
        return {
            'researcher': researcher_html,
            'participants': participant_htmls
        }


def generate_dashboards(
    analysis_results: Dict,
    output_dir: Path = None
) -> Dict[str, str]:
    """
    Generate and save HTML dashboards.
    
    Parameters
    ----------
    analysis_results : Dict
        Complete analysis results from pipeline
    output_dir : Path, optional
        Directory to save dashboard files
        
    Returns
    -------
    Dict[str, str]
        Generated dashboards
    """
    generator = DashboardGenerator()
    dashboards = generator.process(analysis_results)
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save researcher dashboard
        researcher_file = output_dir / "researcher-dashboard.html"
        with open(researcher_file, 'w', encoding='utf-8') as f:
            f.write(dashboards['researcher'])
        
        # Save participant dashboards
        participant_dir = output_dir / "participant-dashboards"
        participant_dir.mkdir(exist_ok=True)
        
        for participant_id, html in dashboards['participants'].items():
            participant_file = participant_dir / f"{participant_id}.html"
            with open(participant_file, 'w', encoding='utf-8') as f:
                f.write(html)
    
    return dashboards


if __name__ == "__main__":
    # Example usage
    import sys
    import json
    
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./processed/dashboards/")
    else:
        results_file = "./processed/analysis_results.json"
        output_path = Path("./processed/dashboards/")
    
    print(f"Generating dashboards from: {results_file}")
    
    try:
        # Load analysis results
        with open(results_file, 'r') as f:
            analysis_results = json.load(f)
        
        # Generate dashboards
        dashboards = generate_dashboards(analysis_results, output_path)
        
        print(f"Generated researcher dashboard and {len(dashboards['participants'])} participant dashboards")
        print(f"Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error generating dashboards: {e}")
        sys.exit(1)
