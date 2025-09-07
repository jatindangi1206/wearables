#!/usr/bin/env python3
"""
Test script for the enhanced GOQII Health Data Pipeline with
integrated meals and lungs data analysis.

Usage:
    python test_integrated_pipeline.py
"""

import sys
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_integrated_pipeline')

def run_test():
    """Run the integrated pipeline test"""
    
    # Import the pipeline runner from main
    try:
        from wearables.main import run_eda_pipeline
    except ImportError:
        logger.error("Failed to import run_eda_pipeline from main.py")
        sys.exit(1)
    
    # Define paths
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    input_dir = current_dir / "input"
    output_dir = current_dir / "processed" / "integrated_test"
    
    logger.info(f"Running integrated pipeline test")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        # Run the pipeline
        results = run_eda_pipeline(
            str(input_dir),
            str(output_dir),
            save_intermediate=True
        )
        
        logger.info("Test completed successfully!")
        logger.info(f"Generated integrated report: {output_dir / 'integrated_report.html'}")
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_test()
