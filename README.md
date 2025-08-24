# GOQII Health Data EDA Protocol

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

A comprehensive **Dual-Output Health Data Analysis System** for GOQII wearable device data, designed to provide both technical research insights and personalized participant feedback.

## 🎯 Overview

This protocol analyzes wearable health data (blood pressure, heart rate, sleep, steps, SpO2, temperature) and generates two distinct outputs:

1. **🔬 Research Analysis**: Technical insights, cohort statistics, data quality metrics
2. **👤 Participant Insights**: Personalized health recommendations, behavioral patterns, progress tracking

## ✨ Key Features

### Data Processing & Quality Control
- 📂 **Smart Data Discovery**: Automatically finds and processes CSV/JSON files
- 🧹 **Comprehensive Cleaning**: Quality flagging, outlier detection, validation ranges
- 📊 **Quality Reporting**: Detailed data completeness and compliance analysis
- 🔄 **Standardization**: Unified data format across all health metrics

### Advanced Analytics
- 🔗 **Correlation Analysis**: 15 metric pairs with daily, lag, and rolling correlations
- 📈 **Anomaly Detection**: Automatic identification with recovery pattern analysis  
- 📊 **Statistical Analysis**: Pearson/Spearman correlations with confidence levels
- 🎯 **Baseline Modeling**: Individual health ranges and temporal patterns

### Dual-Output Dashboards
- 🔬 **Researcher Dashboard**: Cohort analysis, data quality metrics, statistical insights
- 👤 **Participant Dashboard**: Personalized insights, recommendations, progress tracking
- 📱 **Responsive Design**: Beautiful, mobile-friendly HTML dashboards
- 📊 **Interactive Charts**: Baseline distributions, time series, correlation heatmaps

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd goqii_eda

# Install required packages
pip install pandas numpy scipy matplotlib seaborn
```

### Basic Usage

```bash
# Run complete analysis
python main.py ./input_data ./results

# Or with default output directory
python main.py ./input_data
```

### Expected Input Structure

```
input_data/
├── participant-001/
│   ├── bp.csv
│   ├── hr.csv  
│   ├── sleep.csv
│   ├── steps.csv
│   ├── spo2.csv
│   └── temp.csv
├── participant-002/
│   └── ... (same structure)
└── ...
```

### CSV File Format

Each CSV should contain:
```csv
datetime,value,[secondary_value]
2024-01-01 08:00:00,120,80
2024-01-01 12:00:00,125,82
...
```

## 📊 Output Structure

After running the analysis, you'll get:

```
results/
├── 📊 dashboards/
│   ├── 🔬 researcher-dashboard.html          # Technical analysis
│   └── 👥 participant-dashboards/           # Individual reports
│       ├── participant-001.html
│       ├── participant-002.html
│       └── ...
├── 👤 participant_insights/
│   ├── patient-001.json                     # Individual JSON data
│   ├── patient-002.json
│   └── ...  
├── 📋 analysis_results.json                 # Complete results
├── 🧹 cleaning_report.json                  # Data quality report
├── 🔬 technical_analysis.json              # Research insights
├── 🔗 correlation_analysis.json            # Correlation results
└── 📝 logs/                                # Detailed execution logs
```

## 🔍 Analysis Components

### 1. Data Loading & Cleaning (`data_loader.py`, `data_cleaner.py`)
- File discovery and standardization
- Quality control with metric-specific validation
- Outlier detection using Z-score and IQR methods
- Missing data analysis and flagging

### 2. Technical Analysis (`technical_analysis.py`)
- **Missingness Analysis**: Data completeness by participant and metric
- **Compliance Scoring**: Monitoring adherence assessment  
- **Noise Analysis**: Data quality distribution analysis
- **Cohort Analysis**: Population-level statistics and trends

### 3. Correlation Engine (`correlation_engine.py`)
- **Daily Correlations**: Same-day metric relationships (15 pairs)
- **Lag Effects**: Next-day impact analysis
- **Rolling Windows**: 14-day trend correlations
- **Anomaly Detection**: Unusual patterns with recovery analysis

### 4. Participant Insights (`participant_insights.py`)
- **Health Baselines**: Individual normal ranges and patterns
- **Behavioral Insights**: Temporal patterns and habits
- **Personalized Recommendations**: Priority-based action items
- **Progress Tracking**: Improvement trends and stability analysis

### 5. Dashboard Generation (`dashboard.py`)
- **Researcher Dashboard**: Technical overview with quality metrics
- **Participant Dashboards**: Beautiful, personalized health reports
- **Interactive Charts**: Baseline distributions, correlations, time series
- **Export Ready**: Print-friendly HTML format

## 🔧 Technical Architecture

### Core Components

**`core.py`**: Foundation classes
- `HealthDataRecord`: Unified data structure
- `HealthDataCollection`: Data container with participant grouping
- `BaseProcessor`: Consistent processing interface

### Data Flow

```
Raw CSV/JSON Files
    ↓
📂 Data Discovery & Loading
    ↓
🧹 Quality Control & Cleaning  
    ↓
🔬 Technical Analysis ←→ 🔗 Correlation Analysis
    ↓                      ↓
👤 Participant Insights Generation
    ↓
📊 HTML Dashboard Creation
    ↓
💾 Results Export & Logging
```

## 📈 Health Metrics Supported

| Metric | Description | Expected Range | Units |
|--------|-------------|---------------|--------|
| **BP** | Blood Pressure | 90-180 (systolic) | mmHg |
| **HR** | Heart Rate | 40-200 | bpm |
| **Steps** | Daily Step Count | 0-50,000 | steps |
| **Sleep** | Sleep Duration | 0-16 | hours |
| **SpO2** | Oxygen Saturation | 70-100 | % |
| **Temp** | Body Temperature | 95-108 | °F |

## 🎨 Dashboard Features

### Researcher Dashboard
- **Cohort Overview**: Participant count, data quality, compliance scores
- **Quality Metrics**: Completeness by metric, noise analysis
- **Correlation Heatmaps**: Visual correlation matrices
- **Anomaly Summary**: Population-level unusual patterns
- **Participant Table**: Overview of all participants

### Participant Dashboard  
- **Health Summary**: Personal data quality score, monitoring period
- **Key Findings**: Specific insights with actual numbers
- **Health Baselines**: Individual normal ranges with charts
- **Behavioral Patterns**: Temporal insights and habits
- **Recommendations**: Priority-based action items with targets

## ⚙️ Customization

### Validation Ranges
Edit ranges in `data_cleaner.py`:
```python
VALIDATION_RANGES = {
    'bp': {'min': 70, 'max': 250, 'secondary_min': 40, 'secondary_max': 150},
    'hr': {'min': 40, 'max': 200},
    # ... customize as needed
}
```

### Correlation Pairs
Modify pairs in `correlation_engine.py`:
```python
CORRELATION_PAIRS = [
    ('bp', 'hr'),
    ('steps', 'sleep'),  
    # ... add custom pairs
]
```

### Dashboard Styling
Customize CSS in `dashboard.py` methods:
- `_get_research_css()`: Researcher dashboard styles
- `_get_participant_css()`: Participant dashboard styles

## 📝 Logging & Monitoring

The system provides comprehensive logging:
- **Pipeline Progress**: Step-by-step execution status
- **Data Quality Metrics**: Cleaning and validation results
- **Error Handling**: Detailed error traces and recovery
- **Performance Stats**: Processing times and memory usage

## 🔬 Research Applications

Perfect for:
- **Clinical Studies**: Population health trend analysis
- **Wearable Research**: Device validation and comparison
- **Behavioral Analysis**: Activity pattern identification  
- **Intervention Studies**: Before/after comparison analysis
- **Quality Assessment**: Data completeness evaluation

## 👥 Participant Benefits

- **Personalized Insights**: Data-driven health observations
- **Actionable Recommendations**: Priority-based improvement suggestions
- **Progress Tracking**: Trend analysis and goal monitoring
- **Health Education**: Understanding personal patterns
- **Clinical Communication**: Shareable reports for healthcare providers

## 🛠️ Requirements

- **Python**: 3.8+
- **Core Libraries**: pandas, numpy, scipy
- **Visualization**: matplotlib, seaborn  
- **Data Format**: CSV or JSON files
- **Memory**: Minimum 4GB RAM (depends on data size)

## 📊 Performance

- **Processing Speed**: ~1000 records/second
- **Memory Efficient**: Streaming data processing
- **Scalable**: Handles 100+ participants with 10,000+ records each
- **Output Size**: ~5MB per 100 participants (HTML dashboards)

## 📄 Project Structure

```
goqii_eda/
├── 📁 src/
│   ├── core.py                    # Foundation classes
│   ├── data_loader.py             # Data discovery & loading
│   ├── data_cleaner.py            # Quality control & cleaning
│   ├── technical_analysis.py      # Researcher insights
│   ├── correlation_engine.py      # Correlation analysis
│   ├── participant_insights.py    # Personalized insights
│   └── dashboard.py               # HTML dashboard generation
├── 📄 main.py                     # Pipeline orchestrator
├── 📄 README.md                   # This file
├── 📁 input/                      # Raw participant data (create this)
├── 📁 processed/                  # Analysis outputs (generated)
└── 📄 requirements.txt            # Python dependencies
```

---

**Version**: 1.0.0  
**Author**: GOQII EDA Protocol  
**Made with ❤️ for better health data analysis**
