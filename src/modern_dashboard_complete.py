#!/usr/bin/env python3
"""
Complete Modern Health Data Dashboard Generator

A modern implementation using:
- Tailwind CSS for styling
- Heroicons for SVG icons
- anime.js for micro-animations

This replaces the traditional CSS approach with a modern, responsive, and animated dashboard.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ModernDashboardGenerator:
    """
    Complete modern dashboard generator using Tailwind CSS, Heroicons, and anime.js
    """
    
    def __init__(self):
        self.logger = logger
    
    def process(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate modern dashboards from analysis results"""
        
        self.logger.info("Generating modern HTML dashboards with Tailwind CSS")
        
        # Generate researcher dashboard
        researcher_html = self._build_researcher_dashboard(analysis_results)
        
        # Generate participant dashboards
        participant_dashboards = {}
        participant_insights = analysis_results.get('participant_insights', {})
        
        for participant_id, insights in participant_insights.items():
            participant_html = self._build_participant_dashboard(
                participant_id, insights, analysis_results
            )
            participant_dashboards[participant_id] = participant_html
        
        return {
            'researcher': researcher_html,
            'participants': participant_dashboards
        }
    
    def _get_base_template(self) -> str:
        """Get the base HTML template with modern stack includes"""
        return """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Tailwind Configuration -->
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: {{
                            50: '#f0f9ff', 100: '#e0f2fe', 200: '#bae6fd', 300: '#7dd3fc',
                            400: '#38bdf8', 500: '#0ea5e9', 600: '#0284c7', 700: '#0369a1',
                            800: '#075985', 900: '#0c4a6e'
                        }},
                        success: {{
                            50: '#f0fdf4', 100: '#dcfce7', 200: '#bbf7d0', 300: '#86efac',
                            400: '#4ade80', 500: '#22c55e', 600: '#16a34a', 700: '#15803d',
                            800: '#166534', 900: '#14532d'
                        }},
                        warning: {{
                            50: '#fffbeb', 100: '#fef3c7', 200: '#fde68a', 300: '#fcd34d',
                            400: '#fbbf24', 500: '#f59e0b', 600: '#d97706', 700: '#b45309',
                            800: '#92400e', 900: '#78350f'
                        }},
                        error: {{
                            50: '#fef2f2', 100: '#fee2e2', 200: '#fecaca', 300: '#fca5a5',
                            400: '#f87171', 500: '#ef4444', 600: '#dc2626', 700: '#b91c1c',
                            800: '#991b1b', 900: '#7f1d1d'
                        }}
                    }},
                    animation: {{
                        'fade-in': 'fadeIn 0.5s ease-in-out',
                        'slide-in': 'slideIn 0.5s ease-out',
                        'bounce-subtle': 'bounceSubtle 0.6s ease-in-out',
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                    }},
                    keyframes: {{
                        fadeIn: {{
                            '0%': {{ opacity: '0', transform: 'translateY(10px)' }},
                            '100%': {{ opacity: '1', transform: 'translateY(0)' }}
                        }},
                        slideIn: {{
                            '0%': {{ transform: 'translateX(-10px)', opacity: '0' }},
                            '100%': {{ transform: 'translateX(0)', opacity: '1' }}
                        }},
                        bounceSubtle: {{
                            '0%, 100%': {{ transform: 'translateY(-2px)' }},
                            '50%': {{ transform: 'translateY(0)' }}
                        }}
                    }}
                }}
            }}
        }}
    </script>
    
    <!-- anime.js for micro-animations -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
    
    <!-- Custom styles -->
    <style>
        .glass-effect {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        .dark .glass-effect {{
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }}
        
        /* Enhanced card backgrounds for blue gradient */
        .glass-card {{
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border-radius: 16px;
        }}
        
        .glass-card:hover {{
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.4);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            transform: translateY(-4px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .gradient-bg {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .card-hover:hover {{
            transform: translateY(-4px);
            transition: all 0.3s ease;
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #a8a8a8;
        }}
        
        /* Beautiful blue gradient background - original style */
        .blue-gradient {{
            background: linear-gradient(135deg, 
                #667eea 0%,     /* Soft blue */
                #764ba2 25%,    /* Purple-blue */
                #f093fb 50%,    /* Light pink */
                #f5576c 75%,    /* Coral */
                #4facfe 100%    /* Bright blue */
            );
            min-height: 100vh;
            position: relative;
        }}
        
        /* Subtle overlay for better content readability */
        .gradient-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(0.5px);
        }}
    </style>
</head>
<body class="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-blue-900 dark:to-indigo-900 min-h-screen">
{body_content}

<!-- anime.js animations -->
<script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Animate cards on load
        anime({{
            targets: '.animate-card',
            translateY: [20, 0],
            opacity: [0, 1],
            easing: 'easeOutExpo',
            duration: 800,
            delay: anime.stagger(100)
        }});
        
        // Animate stats on load
        anime({{
            targets: '.animate-stat',
            scale: [0.8, 1],
            opacity: [0, 1],
            easing: 'easeOutElastic(1, .8)',
            duration: 1200,
            delay: anime.stagger(150, {{start: 200}})
        }});
        
        // Animate progress bars
        anime({{
            targets: '.progress-bar',
            width: function(el) {{
                return el.getAttribute('data-width') + '%';
            }},
            easing: 'easeInOutQuart',
            duration: 1500,
            delay: 500
        }});
        
        // Hover animations for interactive elements
        document.querySelectorAll('.hover-lift').forEach(element => {{
            element.addEventListener('mouseenter', () => {{
                anime({{
                    targets: element,
                    translateY: -4,
                    scale: 1.02,
                    duration: 300,
                    easing: 'easeOutQuart'
                }});
            }});
            
            element.addEventListener('mouseleave', () => {{
                anime({{
                    targets: element,
                    translateY: 0,
                    scale: 1,
                    duration: 300,
                    easing: 'easeOutQuart'
                }});
            }});
        }});
        
        // Pulse effect for important elements
        anime({{
            targets: '.pulse-glow',
            boxShadow: [
                '0 0 0 0 rgba(59, 130, 246, 0.4)',
                '0 0 0 20px rgba(59, 130, 246, 0)'
            ],
            duration: 2000,
            easing: 'easeOutQuart',
            loop: true
        }});
    }});
</script>

</body>
</html>"""
    
    def _get_heroicon(self, name: str, size: str = "6", stroke_width: str = "1.5") -> str:
        """Get Heroicon SVG markup"""
        
        icons = {
            'heart': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg>',
            'chart-bar': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 00-2-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>',
            'users': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>',
            'calendar': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>',
            'activity': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 00-2-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>',
            'moon': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path></svg>',
            'droplet': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M7.5 7.5h-.75A2.25 2.25 0 004.5 9.75v7.5a2.25 2.25 0 002.25 2.25h7.5a2.25 2.25 0 002.25-2.25v-7.5a2.25 2.25 0 00-2.25-2.25h-.75m0-3l-3-3-3 3m6 6l-3 3-3-3"></path></svg>',
            'thermometer': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
            'shoe-prints': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>',
            'check-circle': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
            'exclamation-triangle': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.94-.833-2.71 0L3.204 16.5c-.77.833.192 2.5 1.732 2.5z"></path></svg>',
            'x-circle': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
            'link': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"></path></svg>',
            'beaker': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5a2.25 2.25 0 00-.659 1.591v3.159a2.25 2.25 0 002.25 2.25h14.159a2.25 2.25 0 002.25-2.25V16.09a2.25 2.25 0 00-.659-1.59L18.25 10.5a2.25 2.25 0 01-.659-1.591V3.104a2.25 2.25 0 00-2.25-2.25H12a2.25 2.25 0 00-2.25 2.25z"></path></svg>',
            'sparkles': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"></path></svg>',
            'eye': f'<svg class="w-{size} h-{size}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="{stroke_width}" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>'
        }
        
        return icons.get(name, f'<div class="w-{size} h-{size} bg-gray-300 rounded"></div>')
    
    def _build_researcher_dashboard(self, data: Dict[str, Any]) -> str:
        """Build the researcher dashboard with comprehensive modern styling"""
        
        # Extract comprehensive data
        loading_report = data.get('data_summary', {}).get('loading_report', {})
        cleaning_report = data.get('data_summary', {}).get('cleaning_report', {})
        technical_analysis = data.get('technical_analysis', {})
        correlation_analysis = data.get('correlation_analysis', {})
        participant_insights = data.get('participant_insights', {})
        
        total_participants = loading_report.get('total_participants', 0)
        date_range = loading_report.get('date_range', {})
        span_days = date_range.get('span_days', 0)
        start_date = date_range.get('start', 'Unknown')
        end_date = date_range.get('end', 'Unknown')
        
        # Calculate comprehensive statistics
        overall_stats = cleaning_report.get('overall_stats', {})
        total_records = overall_stats.get('total_records', 0)
        good_records = overall_stats.get('quality_distribution', {}).get('good', 0)
        data_quality_percentage = overall_stats.get('good_data_percentage', 0)
        
        # Metric availability with detailed stats
        metric_availability = loading_report.get('metric_availability', {})
        metric_stats = cleaning_report.get('metric_stats', {})
        
        body_content = f"""
    <!-- Header -->
    <header class="sticky top-0 z-50 glass-effect">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-6">
                <div class="flex items-center space-x-4">
                    {self._get_heroicon('beaker', '8')}
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
                            GOQII Health Data Analysis
                        </h1>
                        <p class="text-sm text-gray-600 dark:text-gray-300">
                            Research Dashboard - Comprehensive Analysis
                        </p>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-right">
                        <p class="text-sm text-gray-600 dark:text-gray-300">
                            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">
                            KCDH-A, Trivedi School of Biosciences, Ashoka University
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        <!-- Hero Stats - Enhanced -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl hover-lift">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Total Participants
                        </p>
                        <p class="text-3xl font-bold text-primary-600 animate-stat">
                            {total_participants}
                        </p>
                    </div>
                    <div class="text-primary-500 pulse-glow">
                        {self._get_heroicon('users', '12')}
                    </div>
                </div>
            </div>
            
            <div class="animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl hover-lift">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Total Records
                        </p>
                        <p class="text-3xl font-bold text-success-600 animate-stat">
                            {total_records:,}
                        </p>
                    </div>
                    <div class="text-success-500">
                        {self._get_heroicon('chart-bar', '12')}
                    </div>
                </div>
            </div>
            
            <div class="animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl hover-lift">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Analysis Period
                        </p>
                        <p class="text-3xl font-bold text-purple-600 animate-stat">
                            {span_days}
                        </p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">days</p>
                    </div>
                    <div class="text-purple-500">
                        {self._get_heroicon('calendar', '12')}
                    </div>
                </div>
            </div>
            
            <div class="animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl hover-lift">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Data Quality
                        </p>
                        <p class="text-3xl font-bold text-warning-600 animate-stat">
                            {data_quality_percentage:.1f}%
                        </p>
                    </div>
                    <div class="text-warning-500">
                        {self._get_heroicon('check-circle', '12')}
                    </div>
                </div>
            </div>
        </div>

        <!-- Period Information -->
        <div class="mb-8 animate-card bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl p-6">
            <div class="flex items-center space-x-4">
                {self._get_heroicon('calendar', '6')}
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                        Analysis Period
                    </h3>
                    <p class="text-sm text-gray-600 dark:text-gray-300">
                        {start_date} to {end_date} ({span_days} days)
                    </p>
                </div>
            </div>
        </div>

        {self._build_enhanced_data_types_section(metric_availability, metric_stats)}
        {self._build_comprehensive_quality_section(cleaning_report)}
        {self._build_detailed_correlation_section(correlation_analysis)}
        {self._build_technical_analysis_section(technical_analysis)}
        {self._build_enhanced_participant_section(participant_insights)}

    </main>

    <footer class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm mt-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="text-center">
                <p class="text-sm text-gray-600 dark:text-gray-400">
                    Generated by GOQII Health Data EDA Protocol
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    KCDH-A, Trivedi School of Biosciences, Ashoka University
                </p>
            </div>
        </div>
    </footer>
        """
        
        return self._get_base_template().format(
            title="GOQII Health Data - Comprehensive Research Dashboard",
            body_content=body_content
        )
    
    def _build_enhanced_data_types_section(self, metric_availability: Dict[str, str], metric_stats: Dict[str, Any]) -> str:
        """Build enhanced data types availability section with detailed statistics"""
        
        data_types = [
            ('bp', 'Blood Pressure', 'heart', 'text-red-500'),
            ('sleep', 'Sleep Quality', 'moon', 'text-purple-500'),
            ('steps', 'Step Count', 'shoe-prints', 'text-green-500'),
            ('hr', 'Heart Rate', 'activity', 'text-pink-500'),
            ('spo2', 'Blood Oxygen', 'droplet', 'text-blue-500'),
            ('temp', 'Temperature', 'thermometer', 'text-orange-500'),
        ]
        
        html = """
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Data Types & Statistics
            </h2>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-6">
        """
        
        for metric_key, metric_name, icon, color_class in data_types:
            is_available = metric_availability.get(metric_key, '0') != '0'
            metric_data = metric_stats.get(metric_key, {})
            
            if is_available:
                status_class = "bg-white dark:bg-gray-800 border-green-200 dark:border-green-700"
                icon_class = color_class
                text_class = "text-gray-900 dark:text-white"
                indicator = self._get_heroicon('check-circle', '5', '2')
                indicator_class = "text-green-500"
                
                # Extract detailed statistics
                total_records = metric_data.get('total_records', 0)
                good_percentage = metric_data.get('good_data_percentage', 0)
                participants_count = metric_data.get('participants_with_data', 0)
                
            else:
                status_class = "bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 opacity-60"
                icon_class = "text-gray-400"
                text_class = "text-gray-500 dark:text-gray-400"
                indicator = self._get_heroicon('x-circle', '5', '2')
                indicator_class = "text-gray-400"
                total_records = 0
                good_percentage = 0
                participants_count = 0
            
            html += f"""
                <div class="{status_class} rounded-xl p-4 border-2 hover-lift transition-all">
                    <div class="flex items-center justify-between mb-3">
                        <div class="{icon_class}">
                            {self._get_heroicon(icon, '6')}
                        </div>
                        <div class="{indicator_class}">
                            {indicator}
                        </div>
                    </div>
                    <h3 class="font-medium {text_class} text-sm mb-2">
                        {metric_name}
                    </h3>
                    
                    {f'''
                    <div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                        <div class="flex justify-between">
                            <span>Records:</span>
                            <span class="font-medium">{total_records:,}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Quality:</span>
                            <span class="font-medium">{good_percentage:.1f}%</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Participants:</span>
                            <span class="font-medium">{participants_count}</span>
                        </div>
                    </div>
                    ''' if is_available else '<div class="text-xs text-gray-400">No data available</div>'}
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _build_comprehensive_quality_section(self, cleaning_report: Dict[str, Any]) -> str:
        """Build comprehensive data quality analysis section"""
        
        overall_stats = cleaning_report.get('overall_stats', {})
        metric_stats = cleaning_report.get('metric_stats', {})
        participant_stats = cleaning_report.get('participant_stats', {})
        
        if not overall_stats:
            return """
            <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Data Quality Analysis
                </h2>
                <p class="text-gray-600 dark:text-gray-400">
                    No data quality information available.
                </p>
            </div>
            """
        
        total_records = overall_stats.get('total_records', 0)
        quality_distribution = overall_stats.get('quality_distribution', {})
        good_records = quality_distribution.get('good', 0)
        invalid_records = quality_distribution.get('invalid', 0)
        duplicate_records = quality_distribution.get('duplicate', 0)
        outlier_records = quality_distribution.get('outlier', 0)
        
        html = f"""
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Data Quality Analysis
            </h2>
            
            <!-- Overall Statistics -->
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Overall Data Quality</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div class="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-green-600">{good_records:,}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Good Records</div>
                    </div>
                    <div class="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-red-600">{invalid_records:,}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Invalid</div>
                    </div>
                    <div class="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-yellow-600">{duplicate_records:,}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Duplicates</div>
                    </div>
                    <div class="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-orange-600">{outlier_records:,}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Outliers</div>
                    </div>
                </div>
            </div>
            
            <!-- Per-Metric Quality Breakdown -->
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quality by Metric</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        """
        
        metrics = ['steps', 'hr', 'temp', 'bp', 'sleep']
        colors = ['blue', 'pink', 'orange', 'red', 'purple']
        
        for i, metric in enumerate(metrics):
            if metric in metric_stats:
                data = metric_stats[metric]
                total_metric_records = data.get('total_records', 0)
                metric_quality_dist = data.get('quality_distribution', {})
                good_metric_records = metric_quality_dist.get('good', 0)
                percentage = data.get('good_data_percentage', 0)
                
                if percentage >= 80:
                    quality_color = "green"
                elif percentage >= 50:
                    quality_color = "yellow"
                else:
                    quality_color = "red"
                
                color = colors[i]
                
                html += f"""
                <div class="bg-gradient-to-br from-{color}-50 to-{color}-100 dark:from-{color}-900/20 dark:to-{color}-800/20 rounded-xl p-4">
                    <div class="flex items-center justify-between mb-3">
                        <h4 class="font-semibold text-gray-900 dark:text-white capitalize">
                            {metric}
                        </h4>
                        <div class="text-{quality_color}-500">
                            {self._get_heroicon('check-circle' if percentage >= 80 else 'exclamation-triangle', '5')}
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <div class="flex justify-between text-sm mb-1">
                            <span class="text-gray-600 dark:text-gray-400">Quality Score</span>
                            <span class="font-medium text-{quality_color}-600 dark:text-{quality_color}-400">
                                {percentage:.1f}%
                            </span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div class="progress-bar bg-{quality_color}-500 h-2 rounded-full" 
                                 data-width="{percentage}" style="width: 0%"></div>
                        </div>
                    </div>
                    
                    <div class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                        <div class="flex justify-between">
                            <span>Total Records:</span>
                            <span class="font-medium">{total_metric_records:,}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Good Records:</span>
                            <span class="font-medium">{good_metric_records:,}</span>
                        </div>
                    </div>
                </div>
                """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _build_detailed_correlation_section(self, correlation_data: Dict[str, Any]) -> str:
        """Build comprehensive correlation analysis section showing all correlations with detailed interpretations"""
        
        # Load actual correlation analysis data if available
        try:
            import json
            import os
            correlation_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'processed', 'correlation_analysis.json')
            if os.path.exists(correlation_file_path):
                with open(correlation_file_path, 'r') as f:
                    detailed_correlation_data = json.load(f)
            else:
                detailed_correlation_data = correlation_data
        except:
            detailed_correlation_data = correlation_data
        
        html = f"""
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-8 shadow-xl">
            <div class="flex items-center mb-6">
                <div class="text-purple-500 mr-3">
                    {self._get_heroicon('chart-bar-square', '8')}
                </div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
                    Comprehensive Correlation Analysis
                </h2>
            </div>
            
            <div class="mb-6">
                <p class="text-gray-600 dark:text-gray-400">
                    Complete analysis of relationships between health metrics. All correlation tests performed are shown below, 
                    regardless of statistical significance, to provide transparency in the analytical process.
                </p>
            </div>
        """
        
        # Process each participant's correlations
        for participant_id, participant_data in detailed_correlation_data.items():
            if participant_id in ['summary', 'cohort_summary']:
                continue
                
            daily_correlations = participant_data.get('daily_correlations', {})
            data_summary = participant_data.get('data_summary', {})
            
            if not daily_correlations:
                html += f"""
                <div class="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 p-4 mb-6">
                    <p class="text-yellow-800 dark:text-yellow-200">
                        No correlation analysis data available for {participant_id}.
                    </p>
                </div>
                """
                continue
            
            # Calculate statistics
            total_tests = len(daily_correlations)
            significant_count = sum(1 for corr in daily_correlations.values() 
                                  if corr.get('pearson', {}).get('significant') == 'True' or 
                                     corr.get('spearman', {}).get('significant') == 'True')
            potential_trends = sum(1 for corr in daily_correlations.values() 
                                 if corr.get('confidence') in ['might be a thing', 'pretty sure'])
            
            html += f"""
            <div class="mb-8">
                <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                    {participant_id.replace('-', ' ').title()} - All Correlation Tests
                </h3>
                
                <!-- Summary Stats -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-blue-600">{total_tests}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Total Tests</div>
                    </div>
                    <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-green-600">{significant_count}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Significant</div>
                    </div>
                    <div class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-yellow-600">{potential_trends}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Potential Trends</div>
                    </div>
                    <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-purple-600">{data_summary.get('total_days', 0)}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Analysis Days</div>
                    </div>
                </div>
                
                <!-- Correlation Results Grid -->
                <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            """
            
            # Sort correlations by absolute pearson correlation value for better presentation
            sorted_correlations = sorted(
                daily_correlations.items(),
                key=lambda x: abs(x[1].get('pearson', {}).get('r', 0)),
                reverse=True
            )
            
            for correlation_name, correlation_data in sorted_correlations:
                html += self._build_correlation_card(correlation_name, correlation_data)
            
            html += """
                </div>
            </div>
            """
        
        # Add interpretation guide
        html += """
            <div class="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-6">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Understanding Correlation Results
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h5 class="font-medium text-gray-700 dark:text-gray-300 mb-2">Correlation Strength:</h5>
                        <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                            <li><span class="font-medium text-green-600">Strong (|r| ≥ 0.7):</span> Clear relationship</li>
                            <li><span class="font-medium text-yellow-600">Moderate (|r| ≥ 0.4):</span> Noticeable pattern</li>
                            <li><span class="font-medium text-orange-600">Weak (|r| < 0.4):</span> Subtle or no pattern</li>
                        </ul>
                    </div>
                    <div>
                        <h5 class="font-medium text-gray-700 dark:text-gray-300 mb-2">Statistical Significance:</h5>
                        <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                            <li><span class="font-medium text-green-600">p < 0.05:</span> Statistically significant</li>
                            <li><span class="font-medium text-yellow-600">p < 0.1:</span> Marginally significant</li>
                            <li><span class="font-medium text-gray-600">p ≥ 0.1:</span> Not significant</li>
                        </ul>
                    </div>
                </div>
            </div>
        """
        
        html += """
        </div>
        """
        
        return html
                    
        return html
    
    def _build_correlation_card(self, correlation_name: str, correlation_data: Dict[str, Any]) -> str:
        """Build individual correlation analysis card with detailed results"""
        
        # Extract metrics from correlation name
        metrics = correlation_name.replace('_vs_', ' vs ').replace('_', ' ').title()
        
        # Get correlation statistics
        pearson = correlation_data.get('pearson', {})
        spearman = correlation_data.get('spearman', {})
        n_days = correlation_data.get('n_days', 0)
        confidence = correlation_data.get('confidence', 'unknown')
        
        pearson_r = pearson.get('r', 0)
        pearson_p = pearson.get('p_value', 1)
        spearman_r = spearman.get('r', 0)
        spearman_p = spearman.get('p_value', 1)
        
        # Determine significance and styling
        is_significant = pearson.get('significant') == 'True' or spearman.get('significant') == 'True'
        is_marginal = pearson_p < 0.1 or spearman_p < 0.1
        
        if is_significant:
            card_color = "green"
            significance_badge = "Significant"
            border_class = "border-green-200"
        elif is_marginal:
            card_color = "yellow"
            significance_badge = "Marginal"
            border_class = "border-yellow-200"
        else:
            card_color = "gray"
            significance_badge = "Not Significant"
            border_class = "border-gray-200"
        
        # Determine correlation strength
        max_abs_r = max(abs(pearson_r), abs(spearman_r))
        if max_abs_r >= 0.7:
            strength = "Strong"
            strength_color = "green"
        elif max_abs_r >= 0.4:
            strength = "Moderate"
            strength_color = "yellow"
        else:
            strength = "Weak"
            strength_color = "orange"
        
        # Create interpretation
        interpretation = self._get_correlation_interpretation(correlation_name, pearson_r, pearson_p, n_days)
        
        # Correlation visualization (simple progress bar representation)
        pearson_bar_width = min(abs(pearson_r) * 100, 100)
        spearman_bar_width = min(abs(spearman_r) * 100, 100)
        
        return f"""
        <div class="bg-white dark:bg-gray-800 rounded-xl p-6 border-2 {border_class} hover-lift">
            <div class="flex items-center justify-between mb-4">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white">
                    {metrics}
                </h4>
                <span class="px-2 py-1 text-xs font-medium bg-{card_color}-100 text-{card_color}-800 rounded-full">
                    {significance_badge}
                </span>
            </div>
            
            <!-- Sample Size & Confidence -->
            <div class="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-4">
                <span>{n_days} days analyzed</span>
                <span class="capitalize font-medium text-{strength_color}-600">{strength}</span>
            </div>
            
            <!-- Correlation Values -->
            <div class="space-y-3 mb-4">
                <div>
                    <div class="flex justify-between text-sm mb-1">
                        <span class="font-medium text-gray-700 dark:text-gray-300">Pearson (Linear)</span>
                        <span class="font-mono text-{card_color}-600">r = {pearson_r:.3f}</span>
                    </div>
                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div class="bg-{card_color}-500 h-2 rounded-full transition-all duration-500" 
                             style="width: {pearson_bar_width}%"></div>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">p = {pearson_p:.4f}</div>
                </div>
                
                <div>
                    <div class="flex justify-between text-sm mb-1">
                        <span class="font-medium text-gray-700 dark:text-gray-300">Spearman (Rank)</span>
                        <span class="font-mono text-{card_color}-600">ρ = {spearman_r:.3f}</span>
                    </div>
                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div class="bg-{card_color}-500 h-2 rounded-full transition-all duration-500" 
                             style="width: {spearman_bar_width}%"></div>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">p = {spearman_p:.4f}</div>
                </div>
            </div>
            
            <!-- Interpretation -->
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <div class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Interpretation:</div>
                <div class="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                    {interpretation}
                </div>
            </div>
            
            <!-- Confidence Level -->
            <div class="mt-3 text-xs text-center">
                <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full capitalize">
                    Analysis confidence: {confidence}
                </span>
            </div>
        </div>
        """
    
    def _get_correlation_interpretation(self, correlation_name: str, r_value: float, p_value: float, n_days: int) -> str:
        """Generate detailed interpretation for correlation results"""
        
        # Extract metric names
        metrics = correlation_name.replace('_vs_', ' and ').replace('_', ' ')
        
        # Statistical significance
        if p_value < 0.05:
            significance = "statistically significant"
        elif p_value < 0.1:
            significance = "marginally significant"
        else:
            significance = "not statistically significant"
        
        # Correlation strength and direction
        abs_r = abs(r_value)
        if abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.4:
            strength = "moderate"
        else:
            strength = "weak"
        
        direction = "positive" if r_value > 0 else "negative"
        
        # Sample size consideration
        sample_note = ""
        if n_days < 10:
            sample_note = " Note: Small sample size limits reliability of results."
        elif n_days < 20:
            sample_note = " Moderate sample size provides reasonable confidence."
        else:
            sample_note = " Good sample size supports reliable conclusions."
        
        # Build interpretation
        if p_value < 0.05:
            interpretation = f"There is a {strength} {direction} relationship between {metrics} (r={r_value:.3f}, p={p_value:.4f}). This relationship is {significance}."
        else:
            interpretation = f"The analysis shows a {strength} {direction} trend between {metrics} (r={r_value:.3f}), but this relationship is {significance} (p={p_value:.4f}). This could be due to chance or insufficient data."
        
        # Add practical interpretation based on metrics
        if 'steps' in correlation_name and 'sleep' in correlation_name:
            if r_value > 0:
                interpretation += " This suggests that more physical activity might be associated with better sleep patterns."
            else:
                interpretation += " This suggests that higher activity levels might be associated with shorter sleep duration, possibly due to lifestyle factors."
        elif 'heart rate' in correlation_name.lower() or 'hr' in correlation_name:
            if 'steps' in correlation_name and r_value > 0:
                interpretation += " This indicates that more physical activity is associated with elevated heart rate, as expected."
            elif 'temp' in correlation_name:
                interpretation += " This relationship between heart rate and temperature could reflect physiological responses."
        
        interpretation += sample_note
        
        return interpretation
    
    def _build_technical_analysis_section(self, technical_analysis: Dict[str, Any]) -> str:
        """Build technical analysis section with detailed statistics"""
        
        if not technical_analysis:
            return """
            <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Technical Analysis
                </h2>
                <p class="text-gray-600 dark:text-gray-400">
                    No technical analysis data available.
                </p>
            </div>
            """
        
        cohort_summary = technical_analysis.get('cohort_summary', {})
        data_completeness = technical_analysis.get('data_completeness', {})
        
        html = f"""
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Technical Analysis
            </h2>
            
            <!-- Cohort Summary -->
            {f'''
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Cohort Overview</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="space-y-4">
                        {self._format_technical_data("Cohort Summary", cohort_summary)}
                    </div>
                </div>
            </div>
            ''' if cohort_summary else ''}
            
            <!-- Data Completeness -->
            {f'''
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Data Completeness</h3>
                <div class="space-y-3">
                    {self._format_completeness_data(data_completeness)}
                </div>
            </div>
            ''' if data_completeness else ''}
        </div>
        """
        
        return html
    
    def _format_technical_data(self, title: str, data: Any) -> str:
        """Format technical data for display"""
        if isinstance(data, dict):
            html = f'<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">'
            html += f'<h4 class="font-medium text-gray-900 dark:text-white mb-3">{title}</h4>'
            html += '<div class="space-y-2 text-sm">'
            
            for key, value in data.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, (int, float)):
                    if isinstance(value, float):
                        formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = f"{value:,}"
                else:
                    formatted_value = str(value)
                
                html += f'''
                <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">{formatted_key}:</span>
                    <span class="font-medium text-gray-900 dark:text-white">{formatted_value}</span>
                </div>
                '''
            
            html += '</div></div>'
            return html
        else:
            return f'<div class="text-sm text-gray-600 dark:text-gray-400">{data}</div>'
    
    def _format_completeness_data(self, data: Dict[str, Any]) -> str:
        """Format data completeness information"""
        html = ""
        for item_key, completeness in data.items():
            if isinstance(completeness, (int, float)):
                percentage = completeness
                if percentage >= 90:
                    color = "green"
                elif percentage >= 70:
                    color = "yellow"
                else:
                    color = "red"
                
                html += f'''
                <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span class="font-medium text-gray-900 dark:text-white">{item_key.replace('_', ' ').title()}</span>
                    <div class="flex items-center space-x-3">
                        <div class="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div class="progress-bar bg-{color}-500 h-2 rounded-full" 
                                 data-width="{percentage}" style="width: 0%"></div>
                        </div>
                        <span class="text-sm font-medium text-{color}-600 dark:text-{color}-400 w-12">
                            {percentage:.1f}%
                        </span>
                    </div>
                </div>
                '''
        
        return html
    
    def _build_enhanced_participant_section(self, participant_insights: Dict[str, Any]) -> str:
        """Build enhanced participant overview section"""
        
        html = """
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Participant Overview
            </h2>
        """
        
        if not participant_insights:
            html += f"""
            <div class="text-center py-8">
                <div class="text-gray-400 mb-4">
                    {self._get_heroicon('users', '12')}
                </div>
                <p class="text-gray-600 dark:text-gray-400">
                    No participant data available.
                </p>
            </div>
            """
        else:
            html += f"""
            <div class="mb-6">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div class="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-blue-600">{len(participant_insights)}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Total Participants</div>
                    </div>
                    <div class="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-green-600">{sum(len(insights.get('findings', [])) for insights in participant_insights.values())}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Total Findings</div>
                    </div>
                    <div class="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-4 text-center">
                        <div class="text-2xl font-bold text-purple-600">{sum(len(insights.get('recommendations', [])) for insights in participant_insights.values())}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Recommendations</div>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            """
            
            for participant_id, insights in participant_insights.items():
                data_period = insights.get('data_period', {})
                date_range = data_period.get('date_range', {})
                start_date = date_range.get('start', 'Unknown')
                end_date = date_range.get('end', 'Unknown')
                total_days = data_period.get('total_days', 0)
                available_metrics = data_period.get('available_metrics', [])
                
                findings = insights.get('findings', [])
                recommendations = insights.get('recommendations', [])
                
                # Generate avatar with initials
                initials = ''.join([word[0].upper() for word in participant_id.replace('-', ' ').split()])[:2]
                
                html += f"""
                <div class="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-xl p-6 hover-lift">
                    <div class="flex items-center space-x-4 mb-4">
                        <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
                            <span class="text-white font-bold text-sm">{initials}</span>
                        </div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                                {participant_id.replace('-', ' ').title()}
                            </h3>
                            <p class="text-sm text-gray-600 dark:text-gray-400">
                                {start_date} - {end_date} ({total_days} days)
                            </p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600">{len(findings)}</div>
                            <div class="text-xs text-gray-600 dark:text-gray-400">Findings</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600">{len(recommendations)}</div>
                            <div class="text-xs text-gray-600 dark:text-gray-400">Recommendations</div>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <div class="text-xs text-gray-600 dark:text-gray-400 mb-2">Available Metrics:</div>
                        <div class="flex flex-wrap gap-1">
                            {' '.join([f'<span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">{metric.title()}</span>' for metric in available_metrics])}
                        </div>
                    </div>
                    
                    <div class="flex justify-between items-center">
                        <div class="flex space-x-2">
                            <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                Active
                            </span>
                            <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                Complete
                            </span>
                        </div>
                        <div class="text-blue-500 hover:text-blue-600 transition-colors">
                            {self._get_heroicon('eye', '5')}
                        </div>
                    </div>
                </div>
                """
            
            html += """
            </div>
            """
        
        html += """
        </div>
        """
        
        return html
    
    def _build_participant_dashboard(self, participant_id: str, insights: Dict[str, Any], full_data: Dict[str, Any]) -> str:
        """Build comprehensive individual participant dashboard with modern styling"""
        
        # Extract participant data with correct field names
        data_period = insights.get('data_period', {})
        date_range = data_period.get('date_range', {})
        start_date = date_range.get('start', 'Unknown')
        end_date = date_range.get('end', 'Unknown')
        total_days = data_period.get('total_days', 0)
        available_metrics = data_period.get('available_metrics', [])
        
        # Extract detailed insights
        health_baselines = insights.get('health_baselines', {})
        findings = insights.get('findings', [])
        recommendations = insights.get('recommendations', [])
        correlations = insights.get('correlations', [])
        
        # Generate avatar initials
        initials = ''.join([word[0].upper() for word in participant_id.replace('-', ' ').split()])[:2]
        
        body_content = f"""
    <!-- Header -->
    <header class="sticky top-0 z-50 glass-effect">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-6">
                <div class="flex items-center space-x-4">
                    <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                        <span class="text-white font-bold">{initials}</span>
                    </div>
                    <div>
                        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
                            {participant_id.replace('-', ' ').title()}
                        </h1>
                        <p class="text-sm text-gray-600 dark:text-gray-300">
                            Personal Health Dashboard
                        </p>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-right">
                        <p class="text-sm text-gray-600 dark:text-gray-300">
                            Period: {start_date} - {end_date} ({total_days} days)
                        </p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">
                            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        <!-- Overview Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl hover-lift">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Key Findings
                        </p>
                        <p class="text-3xl font-bold text-blue-600 animate-stat">
                            {len(findings)}
                        </p>
                    </div>
                    <div class="text-blue-500 pulse-glow">
                        {self._get_heroicon('sparkles', '10')}
                    </div>
                </div>
            </div>
            
            <div class="animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl hover-lift">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Recommendations
                        </p>
                        <p class="text-3xl font-bold text-green-600 animate-stat">
                            {len(recommendations)}
                        </p>
                    </div>
                    <div class="text-green-500">
                        {self._get_heroicon('check-circle', '10')}
                    </div>
                </div>
            </div>
            
            <div class="animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl hover-lift">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Data Types
                        </p>
                        <p class="text-3xl font-bold text-purple-600 animate-stat">
                            {len(available_metrics)}
                        </p>
                    </div>
                    <div class="text-purple-500">
                        {self._get_heroicon('chart-bar', '10')}
                    </div>
                </div>
            </div>
            
            <div class="animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl hover-lift">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Monitoring Days
                        </p>
                        <p class="text-3xl font-bold text-orange-600 animate-stat">
                            {total_days}
                        </p>
                    </div>
                    <div class="text-orange-500">
                        {self._get_heroicon('calendar', '10')}
                    </div>
                </div>
            </div>
        </div>

        <!-- Health Baselines Section -->
        {self._build_health_baselines_section(health_baselines)}

        <!-- Key Findings -->
        {self._build_findings_section(findings)}

        <!-- Recommendations -->
        {self._build_recommendations_section(recommendations)}

        <!-- Health Metrics Overview -->
        {self._build_participant_health_metrics_section(available_metrics, health_baselines)}

        <!-- Correlations -->
        {self._build_participant_correlations_section(correlations)}

    </main>

    <footer class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm mt-16">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="text-center">
                <p class="text-sm text-gray-600 dark:text-gray-400">
                    Personal Health Dashboard - GOQII Health Data Analysis
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    KCDH-A, Trivedi School of Biosciences, Ashoka University
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    This report is for informational purposes only. Please consult your healthcare provider for medical advice.
                </p>
            </div>
        </div>
    </footer>
        """
        
        return self._get_base_template().format(
            title=f"GOQII Health Data - {participant_id.replace('-', ' ').title()}",
            body_content=body_content
        )
    
    def _build_health_baselines_section(self, health_baselines: Dict[str, Any]) -> str:
        """Build health baselines section with detailed statistics"""
        
        if not health_baselines:
            return f"""
            <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Health Baselines
                </h2>
                <div class="text-center py-8">
                    <div class="text-gray-400 mb-4">
                        {self._get_heroicon('chart-bar', '12')}
                    </div>
                    <p class="text-gray-600 dark:text-gray-400">
                        No baseline data available.
                    </p>
                </div>
            </div>
            """
        
        html = """
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Health Baselines & Statistics
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        """
        
        metric_icons = {
            'sleep': ('moon', 'purple'),
            'hr': ('heart', 'red'),
            'temp': ('thermometer', 'orange'),
            'bp': ('activity', 'blue'),
            'steps': ('shoe-prints', 'green'),
            'spo2': ('droplet', 'cyan')
        }
        
        for metric_name, baseline_data in health_baselines.items():
            if isinstance(baseline_data, dict):
                icon, color = metric_icons.get(metric_name, ('chart-bar', 'gray'))
                
                count = baseline_data.get('count', 0)
                mean = baseline_data.get('mean', 0)
                median = baseline_data.get('median', 0)
                std = baseline_data.get('std', 0)
                interpretation = baseline_data.get('interpretation', 'No interpretation available')
                normal_range = baseline_data.get('normal_range', {})
                
                html += f"""
                <div class="bg-gradient-to-br from-{color}-50 to-{color}-100 dark:from-{color}-900/20 dark:to-{color}-800/20 rounded-xl p-6 hover-lift">
                    <div class="flex items-center mb-4">
                        <div class="text-{color}-500 mr-3">
                            {self._get_heroicon(icon, '6')}
                        </div>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                            {metric_name.replace('_', ' ').title()}
                        </h3>
                    </div>
                    
                    <div class="space-y-3 mb-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="text-center">
                                <div class="text-xl font-bold text-{color}-600">{mean:.1f}</div>
                                <div class="text-xs text-gray-600 dark:text-gray-400">Average</div>
                            </div>
                            <div class="text-center">
                                <div class="text-xl font-bold text-{color}-600">{median:.1f}</div>
                                <div class="text-xs text-gray-600 dark:text-gray-400">Median</div>
                            </div>
                        </div>
                        
                        <div class="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                            <div class="flex justify-between">
                                <span>Records:</span>
                                <span class="font-medium">{count:,}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Std Dev:</span>
                                <span class="font-medium">{std:.2f}</span>
                            </div>
                            {f'''
                            <div class="flex justify-between">
                                <span>Normal Range:</span>
                                <span class="font-medium">{normal_range.get("lower", "N/A")}-{normal_range.get("upper", "N/A")}</span>
                            </div>
                            ''' if normal_range else ''}
                        </div>
                    </div>
                    
                    <div class="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
                        <div class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Interpretation:</div>
                        <div class="text-xs text-gray-600 dark:text-gray-400">{interpretation}</div>
                    </div>
                </div>
                """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _build_participant_health_metrics_section(self, available_metrics: List[str], health_baselines: Dict[str, Any]) -> str:
        """Build participant health metrics overview section"""
        
        html = """
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Your Health Metrics Overview
            </h2>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        """
        
        # Define all possible metrics with their display info
        all_metrics = {
            'steps': ('Steps', 'shoe-prints', 'green', 'avg/day'),
            'hr': ('Heart Rate', 'heart', 'red', 'avg bpm'),
            'sleep': ('Sleep', 'moon', 'purple', 'avg hours'),
            'bp': ('Blood Pressure', 'activity', 'blue', 'avg mmHg'),
            'spo2': ('SpO2', 'droplet', 'cyan', 'avg %'),
            'temp': ('Temperature', 'thermometer', 'orange', 'avg °F')
        }
        
        for metric_key, (name, icon, color, unit) in all_metrics.items():
            is_available = metric_key in available_metrics
            baseline_data = health_baselines.get(metric_key, {}) if is_available else {}
            
            if is_available and baseline_data:
                mean_value = baseline_data.get('mean', 0)
                
                # Format value based on metric type
                if metric_key == 'steps':
                    display_value = f"{int(mean_value):,}"
                elif metric_key == 'bp':
                    # For BP, we might need to handle systolic/diastolic differently
                    display_value = f"{mean_value:.0f}"
                elif metric_key == 'temp':
                    display_value = f"{mean_value:.1f}°F"
                elif metric_key == 'spo2':
                    display_value = f"{mean_value:.1f}%"
                else:
                    display_value = f"{mean_value:.1f}"
                
                opacity_class = ""
                bg_class = f"bg-gradient-to-br from-{color}-50 to-{color}-100 dark:from-{color}-900/20 dark:to-{color}-800/20"
            else:
                display_value = "N/A"
                opacity_class = "opacity-50"
                bg_class = "bg-gray-50 dark:bg-gray-800"
            
            html += f"""
                <div class="{bg_class} rounded-xl p-4 text-center hover-lift {opacity_class}">
                    <div class="text-{color}-500 mb-2 flex justify-center">
                        {self._get_heroicon(icon, '8')}
                    </div>
                    <div class="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                        {display_value}
                    </div>
                    <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        {name}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                        {unit}
                    </div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _build_participant_correlations_section(self, correlations: List[Dict[str, Any]]) -> str:
        """Build comprehensive participant correlations section showing all correlation analyses"""
        
        # Load actual correlation analysis data if available
        try:
            import json
            import os
            correlation_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'processed', 'correlation_analysis.json')
            if os.path.exists(correlation_file_path):
                with open(correlation_file_path, 'r') as f:
                    detailed_correlation_data = json.load(f)
                # Extract participant-1 data
                participant_correlations = detailed_correlation_data.get('participant-1', {}).get('daily_correlations', {})
            else:
                participant_correlations = {}
        except:
            participant_correlations = {}
        
        # If no detailed data available, fall back to provided correlations
        if not participant_correlations and isinstance(correlations, list):
            # Convert list format to dict format for consistency
            participant_correlations = {}
            for i, corr in enumerate(correlations):
                if isinstance(corr, dict):
                    participant_correlations[f"correlation_{i}"] = corr
        
        html = f"""
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <div class="flex items-center mb-6">
                <div class="text-purple-500 mr-3">
                    {self._get_heroicon('link', '8')}
                </div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
                    Your Health Metric Correlations
                </h2>
            </div>
            
            <div class="mb-6">
                <p class="text-gray-600 dark:text-gray-400">
                    These correlations show how your different health metrics relate to each other. All analyses performed are shown below for complete transparency.
                </p>
            </div>
        """
        
        if not participant_correlations:
            html += f"""
            <div class="text-center py-8">
                <div class="text-gray-400 mb-4">
                    {self._get_heroicon('link', '12')}
                </div>
                <p class="text-gray-600 dark:text-gray-400">
                    No correlation analysis data available for your health metrics.
                </p>
            </div>
        """
        else:
            # Calculate summary statistics
            total_tests = len(participant_correlations)
            significant_count = sum(1 for corr in participant_correlations.values() 
                                  if corr.get('pearson', {}).get('significant') == 'True' or 
                                     corr.get('spearman', {}).get('significant') == 'True')
            potential_trends = sum(1 for corr in participant_correlations.values() 
                                 if corr.get('confidence') in ['might be a thing', 'pretty sure'])
            
            html += f"""
            <!-- Summary Statistics -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-blue-600">{total_tests}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Tests Performed</div>
                </div>
                <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-green-600">{significant_count}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Significant</div>
                </div>
                <div class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-yellow-600">{potential_trends}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Potential Patterns</div>
                </div>
                <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-purple-600">{significant_count/total_tests*100 if total_tests > 0 else 0:.0f}%</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Success Rate</div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            """
            
            # Sort correlations by absolute correlation strength
            sorted_correlations = sorted(
                participant_correlations.items(),
                key=lambda x: abs(x[1].get('pearson', {}).get('r', 0)),
                reverse=True
            )
            
            for correlation_name, correlation_data in sorted_correlations:
                # Use the same correlation card builder as the research dashboard
                html += self._build_correlation_card(correlation_name, correlation_data)
            
            html += """
            </div>
            
            <!-- Personal Insights -->
            <div class="mt-8 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl p-6">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    What This Means For You
                </h4>
                <div class="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                    <p>• <strong>Significant correlations</strong> indicate reliable patterns in your health data that could guide lifestyle decisions.</p>
                    <p>• <strong>Non-significant results</strong> don't mean there's no relationship - it could mean more data is needed or the relationship is more complex.</p>
                    <p>• <strong>Correlation doesn't imply causation</strong> - these patterns show associations, not necessarily cause-and-effect relationships.</p>
                    <p>• Use these insights alongside professional medical advice for the best health outcomes.</p>
                </div>
            </div>
            """
        
        html += """
        </div>
        """
        
        return html
    
    def _build_findings_section(self, findings: List[Dict[str, Any]]) -> str:
        """Build the key findings section"""
        
        if not findings:
            return f"""
            <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Key Findings
                </h2>
                <div class="text-center py-8">
                    <div class="text-gray-400 mb-4">
                        {self._get_heroicon('sparkles', '12')}
                    </div>
                    <p class="text-gray-600 dark:text-gray-400">
                        No significant findings identified.
                    </p>
                </div>
            </div>
            """
        
        html = """
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Key Findings
            </h2>
            <div class="space-y-4">
        """
        
        for i, finding in enumerate(findings):
            title = finding.get('title', f'Finding {i+1}')
            description = finding.get('description', 'No description available')
            priority = finding.get('priority', 'medium').lower()
            
            if priority == 'high':
                color_class = "red"
                icon = "exclamation-triangle"
            elif priority == 'low':
                color_class = "green"
                icon = "check-circle"
            else:
                color_class = "blue"
                icon = "sparkles"
            
            html += f"""
                <div class="bg-gradient-to-r from-{color_class}-50 to-{color_class}-100 dark:from-{color_class}-900/20 dark:to-{color_class}-800/20 rounded-xl p-4 hover-lift">
                    <div class="flex items-start space-x-3">
                        <div class="text-{color_class}-500 mt-1">
                            {self._get_heroicon(icon, '5')}
                        </div>
                        <div class="flex-1">
                            <h3 class="font-semibold text-gray-900 dark:text-white mb-1">
                                {title}
                            </h3>
                            <p class="text-sm text-gray-600 dark:text-gray-400">
                                {description}
                            </p>
                            <span class="inline-block mt-2 px-2 py-1 bg-{color_class}-100 text-{color_class}-800 text-xs rounded-full">
                                {priority.title()} Priority
                            </span>
                        </div>
                    </div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _build_recommendations_section(self, recommendations: List[Dict[str, Any]]) -> str:
        """Build the recommendations section"""
        
        if not recommendations:
            return f"""
            <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Health Recommendations
                </h2>
                <div class="text-center py-8">
                    <div class="text-gray-400 mb-4">
                        {self._get_heroicon('check-circle', '12')}
                    </div>
                    <p class="text-gray-600 dark:text-gray-400">
                        No specific recommendations at this time.
                    </p>
                </div>
            </div>
            """
        
        html = """
        <div class="mb-8 animate-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Health Recommendations
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        """
        
        for i, recommendation in enumerate(recommendations):
            title = recommendation.get('title', f'Recommendation {i+1}')
            description = recommendation.get('description', 'No description available')
            category = recommendation.get('category', 'general').lower()
            
            # Map categories to colors and icons
            category_map = {
                'exercise': ('green', 'shoe-prints'),
                'sleep': ('purple', 'moon'),
                'diet': ('orange', 'heart'),
                'general': ('blue', 'sparkles'),
                'medical': ('red', 'beaker')
            }
            
            color_class, icon = category_map.get(category, ('blue', 'sparkles'))
            
            html += f"""
                <div class="bg-gradient-to-br from-{color_class}-50 to-{color_class}-100 dark:from-{color_class}-900/20 dark:to-{color_class}-800/20 rounded-xl p-4 hover-lift">
                    <div class="flex items-start space-x-3">
                        <div class="text-{color_class}-500 mt-1">
                            {self._get_heroicon(icon, '6')}
                        </div>
                        <div class="flex-1">
                            <h3 class="font-semibold text-gray-900 dark:text-white mb-2">
                                {title}
                            </h3>
                            <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                                {description}
                            </p>
                            <div class="flex justify-between items-center">
                                <span class="px-2 py-1 bg-{color_class}-100 text-{color_class}-800 text-xs rounded-full">
                                    {category.title()}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    



# Integration function to generate dashboards
def generate_modern_dashboards(analysis_results: Dict[str, Any], output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate modern dashboards using Tailwind CSS, Heroicons, and anime.js
    """
    generator = ModernDashboardGenerator()
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
    
    print(f"🎨 Generating modern dashboards from: {results_file}")
    
    try:
        # Load analysis results
        with open(results_file, 'r') as f:
            analysis_results = json.load(f)
        
        # Generate dashboards
        dashboards = generate_modern_dashboards(analysis_results, output_path)
        
        print(f"✅ Generated modern researcher dashboard and {len(dashboards['participants'])} participant dashboards")
        print(f"📂 Output saved to: {output_path}")
        print(f"🎨 Stack: Tailwind CSS + Heroicons + anime.js")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
