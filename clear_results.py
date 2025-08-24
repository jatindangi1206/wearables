#!/usr/bin/env python3
"""
Clear Results Script for GOQII EDA Pipeline
Removes all generated analysis outputs to prepare for new participant data
"""

import os
import shutil
import sys
from pathlib import Path

def clear_results(base_dir="./processed"):
    """Clear all analysis results and outputs"""
    
    processed_path = Path(base_dir)
    
    if not processed_path.exists():
        print(f"✅ No results to clear - {base_dir} doesn't exist")
        return
    
    print(f"🧹 Clearing results from: {processed_path.absolute()}")
    
    # List of items to remove
    items_to_remove = [
        "analysis_results.json",
        "cleaning_report.json", 
        "correlation_analysis.json",
        "raw_data_summary.json",
        "technical_analysis.json",
        "dashboards/",
        "logs/",
        "participant/",
        "participant_insights/",
        "technical/"
    ]
    
    removed_count = 0
    
    for item in items_to_remove:
        item_path = processed_path / item
        
        if item_path.exists():
            try:
                if item_path.is_file():
                    item_path.unlink()
                    print(f"  ❌ Removed file: {item}")
                    removed_count += 1
                elif item_path.is_dir():
                    shutil.rmtree(item_path)
                    print(f"  📁 Removed directory: {item}")
                    removed_count += 1
            except Exception as e:
                print(f"  ⚠️  Warning: Could not remove {item}: {e}")
    
    # Remove the processed directory if it's empty
    try:
        if processed_path.exists() and not any(processed_path.iterdir()):
            processed_path.rmdir()
            print(f"  📂 Removed empty processed directory")
            removed_count += 1
    except:
        pass
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} items")
    print("🚀 Ready for new participant data analysis")

if __name__ == "__main__":
    # Allow custom output directory
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./processed"
    
    print("=" * 60)
    print("🧹 GOQII EDA PIPELINE - RESULTS CLEANER")
    print("=" * 60)
    
    clear_results(output_dir)
    
    print("\n" + "=" * 60)
