"""
GOQII Health Data EDA Protocol - Main Pipeline

Complete orchestration script for the dual-output health data analysis:
- Research Analysis: Technical insights, cohort statistics, quality control
- Participant Insights: Personalized recommendations, health baselines, behavioral patterns

Usage:
    python main.py <input_directory> [output_directory]
    
Example:
    python main.py ./input ./processed
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Import all modules
from wearables.src.core import HealthDataCollection
from wearables.src.data_loader import load_goqii_data
from wearables.src.data_cleaner import clean_goqii_data
from wearables.src.technical_analysis import generate_technical_analysis
from wearables.src.correlation_engine import generate_correlation_analysis, analyze_deviations
from wearables.src.participant_insights import generate_participant_insights
from wearables.src.modern_dashboard_complete import generate_modern_dashboards
from wearables.src.integrated_report_helpers import generate_integrated_report


def setup_logging(output_dir: Path) -> logging.Logger:
    """Setup comprehensive logging"""
    
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('goqii_eda')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    log_file = log_dir / f"eda_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def save_analysis_results(results: Dict, output_dir: Path) -> None:
    """Save complete analysis results to JSON"""
    
    results_file = output_dir / "analysis_results.json"
    
    # Convert any non-serializable objects to strings
    def serialize_results(obj):
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # custom objects
            return str(obj)
        else:
            return str(obj)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=serialize_results, ensure_ascii=False)
    
    logger.info(f"Analysis results saved to: {results_file}")


def run_eda_pipeline(
    input_dir: str,
    output_dir: str = "./processed",
    save_intermediate: bool = True
) -> Dict:
    """
    Run complete GOQII Health Data EDA Pipeline.
    
    Parameters
    ----------
    input_dir : str
        Directory containing GOQII health data files
    output_dir : str
        Directory to save all outputs
    save_intermediate : bool
        Whether to save intermediate results
        
    Returns
    -------
    Dict
        Complete analysis results
    """
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    global logger
    logger = setup_logging(output_path)
    
    logger.info("="*80)
    logger.info("GOQII HEALTH DATA EDA PROTOCOL - DUAL OUTPUT ANALYSIS")
    logger.info("="*80)
    logger.info(f"Input Directory: {input_dir}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Pipeline Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # =============================================================================
        # STEP 1: DATA LOADING AND DISCOVERY
        # =============================================================================
        logger.info("\n📂 STEP 1: Data Loading and Discovery")
        logger.info("-" * 50)
        
        raw_data, loading_report, meals_data, lungs_data = load_goqii_data(input_dir)
        
        logger.info(f"✅ Discovered data for {len(raw_data.get_participants())} participants")
        logger.info(f"📊 Total physio records loaded: {len(raw_data.records):,}")
        logger.info(f"🍲 Meals data records: {len(meals_data) if meals_data is not None else 0}")
        logger.info(f"🫁 Lungs data records: {len(lungs_data) if lungs_data is not None else 0}")
        logger.info(f"📁 Files processed: {loading_report.get('files_processed', 0)}")
        logger.info(f"🗓️  Date range: {loading_report.get('date_range', {}).get('start', 'N/A')} to {loading_report.get('date_range', {}).get('end', 'N/A')}")
        
        if save_intermediate:
            raw_file = output_path / "raw_data_summary.json"
            with open(raw_file, 'w') as f:
                json.dump(loading_report, f, indent=2, default=str)
        
        # =============================================================================
        # STEP 2: DATA CLEANING AND QUALITY CONTROL
        # =============================================================================
        logger.info("\n🧹 STEP 2: Data Cleaning and Quality Control")
        logger.info("-" * 50)
        
        cleaned_data, cleaning_report = clean_goqii_data(raw_data)
        
        total_clean = sum(1 for r in cleaned_data.records if r.quality_flag == 'good')
        total_flagged = len(cleaned_data.records) - total_clean
        quality_pct = (total_clean / len(cleaned_data.records)) * 100 if cleaned_data.records else 0
        
        logger.info(f"✅ Data cleaning completed")
        logger.info(f"📊 Clean records: {total_clean:,} ({quality_pct:.1f}%)")
        logger.info(f"⚠️  Flagged records: {total_flagged:,}")
        
        # Log quality by metric
        for metric, quality_stats in cleaning_report.get('quality_by_metric', {}).items():
            clean_pct = quality_stats.get('clean_percentage', 0)
            logger.info(f"   {metric}: {clean_pct:.1f}% clean data")
        
        if save_intermediate:
            clean_file = output_path / "cleaning_report.json"
            with open(clean_file, 'w') as f:
                json.dump(cleaning_report, f, indent=2, default=str)
        
        # =============================================================================
        # STEP 3: TECHNICAL ANALYSIS (RESEARCHER INSIGHTS)
        # =============================================================================
        logger.info("\n🔬 STEP 3: Technical Analysis for Researchers")
        logger.info("-" * 50)
        
        technical_results = generate_technical_analysis(cleaned_data)
        
        logger.info(f"✅ Technical analysis completed")
        
        # Log key technical findings
        missingness = technical_results.get('missingness_analysis', {})
        if missingness:
            logger.info("📊 Data Completeness by Metric:")
            for metric, miss_data in missingness.items():
                completeness = 100 - miss_data.get('missing_percentage', 0)
                logger.info(f"   {metric}: {completeness:.1f}% complete")
        
        cohort_analysis = technical_results.get('cohort_analysis', {})
        avg_quality = cohort_analysis.get('average_data_quality', 0)
        avg_compliance = cohort_analysis.get('average_compliance', 0)
        logger.info(f"📈 Cohort average data quality: {avg_quality:.1f}%")
        logger.info(f"📈 Cohort average compliance: {avg_compliance:.1f}%")
        
        if save_intermediate:
            tech_file = output_path / "technical_analysis.json"
            with open(tech_file, 'w') as f:
                json.dump(technical_results, f, indent=2, default=str)
        
        # =============================================================================
        # STEP 4: CORRELATION ANALYSIS
        # =============================================================================
        logger.info("\n🔗 STEP 4: Correlation Analysis")
        logger.info("-" * 50)
        
        correlation_results = generate_correlation_analysis(cleaned_data)
        
        total_significant = 0
        total_correlations = 0
        
        for participant_id, participant_corr in correlation_results.items():
            daily_corr = participant_corr.get('daily_correlations', {})
            for corr_name, corr_data in daily_corr.items():
                total_correlations += 1
                if corr_data.get('pearson', {}).get('significant', False):
                    total_significant += 1
        
        sig_pct = (total_significant / total_correlations) * 100 if total_correlations > 0 else 0
        
        logger.info(f"✅ Correlation analysis completed")
        logger.info(f"📊 Total correlations analyzed: {total_correlations:,}")
        logger.info(f"📈 Significant correlations found: {total_significant} ({sig_pct:.1f}%)")
        
        if save_intermediate:
            corr_file = output_path / "correlation_analysis.json"
            with open(corr_file, 'w') as f:
                json.dump(correlation_results, f, indent=2, default=str)
        
        # =============================================================================
        # STEP 5: PARTICIPANT INSIGHTS (PERSONALIZED ANALYSIS)
        # =============================================================================
        logger.info("\n👤 STEP 5: Participant Insights Generation")
        logger.info("-" * 50)
        
        participant_dir = output_path / "participant_insights"
        participant_results = generate_participant_insights(cleaned_data, participant_dir)
        
        logger.info(f"✅ Participant insights generated")
        logger.info(f"👥 Participants analyzed: {len(participant_results)}")
        
        # Log sample insights
        for participant_id, insights in list(participant_results.items())[:3]:  # First 3
            key_findings = insights.get('personalized_insights', {}).get('key_findings', [])
            recommendations = insights.get('personalized_insights', {}).get('recommendations', [])
            
            logger.info(f"   {participant_id}: {len(key_findings)} findings, {len(recommendations)} recommendations")
        
        # =============================================================================
        # STEP 6: DASHBOARD GENERATION
        # =============================================================================
        logger.info("\n📊 STEP 6: HTML Dashboard Generation")
        logger.info("-" * 50)
        
        # Combine all results
        combined_results = {
            'pipeline_info': {
                'version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'input_directory': input_dir,
                'output_directory': output_dir,
            },
            'data_summary': {
                'loading_report': loading_report,
                'cleaning_report': cleaning_report,
            },
            'technical_analysis': technical_results,
            'correlation_analysis': correlation_results,
            'participant_insights': participant_results,
        }
        
        # Generate dashboards
        dashboard_dir = output_path / "dashboards"
        dashboards = generate_modern_dashboards(combined_results, dashboard_dir)
        
        logger.info(f"✅ Dashboard generation completed")
        logger.info(f"📈 Researcher dashboard created: {dashboard_dir / 'researcher-dashboard.html'}")
        logger.info(f"👥 Participant dashboards created: {len(dashboards['participants'])}")
        
        # =============================================================================
        # STEP 7: INTEGRATED REPORT GENERATION
        # =============================================================================
        logger.info("\n📊 STEP 7: Integrated Report Generation")
        logger.info("-" * 50)
        
        # Generate deviations analysis
        logger.info("Generating deviations analysis...")
        deviations_analysis = analyze_deviations(cleaned_data, meals_data)
        
        # Generate integrated report with all data
        logger.info("Generating integrated HTML report...")
        integrated_report_path = generate_integrated_report(
            cleaned_data,
            meals_data,
            lungs_data,
            technical_results,
            correlation_results,
            output_dir=output_dir
        )
        
        logger.info(f"Integrated report generated: {integrated_report_path}")
        
        # =============================================================================
        # STEP 8: FINAL RESULTS COMPILATION
        # =============================================================================
        logger.info("\n📋 STEP 8: Results Compilation")
        logger.info("-" * 50)
        
        # Add dashboard info to results
        combined_results['dashboards_generated'] = {
            'researcher_dashboard': str(dashboard_dir / 'researcher-dashboard.html'),
            'participant_dashboards': len(dashboards['participants']),
            'dashboard_directory': str(dashboard_dir),
            'integrated_report': str(integrated_report_path)
        }
        
        # Save complete results
        save_analysis_results(combined_results, output_path)
        
        # =============================================================================
        # PIPELINE COMPLETION SUMMARY
        # =============================================================================
        logger.info("\n" + "="*80)
        logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        logger.info(f"📊 RESEARCHER INSIGHTS:")
        logger.info(f"   • Analyzed {len(raw_data.get_participants())} participants")
        logger.info(f"   • Processed {len(raw_data.records):,} total records")
        logger.info(f"   • Achieved {quality_pct:.1f}% data quality")
        logger.info(f"   • Found {total_significant} significant correlations")
        logger.info(f"   • Research dashboard: {dashboard_dir / 'researcher-dashboard.html'}")
        
        logger.info(f"\n👥 PARTICIPANT INSIGHTS:")
        logger.info(f"   • Generated personalized insights for {len(participant_results)} participants")
        logger.info(f"   • Individual reports saved to: {participant_dir}")
        logger.info(f"   • Interactive dashboards saved to: {dashboard_dir / 'participant-dashboards'}")
        
        logger.info(f"\n📁 OUTPUT STRUCTURE:")
        logger.info(f"   📂 {output_path}/")
        logger.info(f"   ├── 📊 dashboards/")
        logger.info(f"   │   ├── 🔬 researcher-dashboard.html")
        logger.info(f"   │   └── 👥 participant-dashboards/")
        logger.info(f"   ├── � integrated_report.html")
        logger.info(f"   ├── �👤 participant_insights/")
        logger.info(f"   ├── 📋 analysis_results.json")
        logger.info(f"   └── 📝 logs/")
        
        logger.info(f"\n⏱️  Pipeline completed in: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        return combined_results
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed with error: {str(e)}")
        logger.exception("Full error traceback:")
        raise


def main():
    """Main entry point for the EDA pipeline"""
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_directory> [output_directory]")
        print("\nExample:")
        print("  python main.py ./input")
        print("  python main.py ./input ./my_analysis")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else "./processed"
    
    # Validate input directory
    if not Path(input_directory).exists():
        print(f"❌ Error: Input directory '{input_directory}' does not exist")
        sys.exit(1)
    
    try:
        # Run the complete pipeline
        results = run_eda_pipeline(input_directory, output_directory)
        
        print("\n🎉 SUCCESS! GOQII Health Data EDA Protocol completed successfully.")
        print(f"\n📂 Check your results in: {output_directory}")
        print(f"📊 Researcher Dashboard: {output_directory}/dashboards/researcher-dashboard.html")
        print(f"� Integrated Report: {output_directory}/integrated_report.html")
        print(f"�👥 Participant Dashboards: {output_directory}/dashboards/participant-dashboards/")
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        print("Check the log files for detailed error information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
