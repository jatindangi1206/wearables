def _generate_deviations_html(self, deviations_analysis) -> str:
        """Generate HTML for deviations analysis"""
        
        if not deviations_analysis or not isinstance(deviations_analysis, dict):
            return '<p class="text-gray-500">No deviation data available.</p>'
        
        deviations_html = """
        <div class="space-y-4">
        """
        
        # Check for significant changes
        significant_changes = deviations_analysis.get('significant_changes', [])
        meal_correlations = deviations_analysis.get('meal_correlations', [])
        metrics_info = deviations_analysis.get('metrics', {})
        
        if not significant_changes:
            return '<p class="text-gray-500">No significant deviations detected.</p>'
        
        # Map meals to dates for easier lookup
        meals_by_date = {}
        for meal_corr in meal_correlations:
            date = meal_corr.get('date')
            if date:
                if date not in meals_by_date:
                    meals_by_date[date] = []
                meals_by_date[date].append(meal_corr.get('meal', 'Unknown'))
        
        # Group changes by date
        changes_by_date = {}
        for change in significant_changes:
            date_str = change.get('date', 'Unknown')
            if date_str not in changes_by_date:
                changes_by_date[date_str] = []
            changes_by_date[date_str].append(change)
        
        # Process each date with deviations
        for date_str, changes in changes_by_date.items():
            # Get meals for this date
            meals_list = meals_by_date.get(date_str, [])
            meals_str = ", ".join(meals_list) if meals_list else "No meals recorded"
            
            deviations_html += f"""
            <div class="bg-white rounded-lg shadow-md p-4 mb-4">
                <h3 class="text-lg font-semibold mb-2">Deviations on {date_str}</h3>
                <p class="mb-3 text-gray-600"><strong>Meals:</strong> {meals_str}</p>
                <div class="space-y-3">
            """
            
            # Process each metric deviation for this date
            for change in changes:
                metric_name = change.get('metric', 'Unknown')
                value = change.get('value', 0)
                z_score = change.get('z_score', 0)
                direction = change.get('direction', 'unknown')
                
                # Get baseline metrics if available
                metric_info = metrics_info.get(metric_name, {})
                mean_val = metric_info.get('mean', 0)
                
                # Calculate deviation percentage
                deviation_pct = ((value - mean_val) / mean_val * 100) if mean_val != 0 else 0
                outside_threshold = abs(z_score) > 1.5
                
                # Format display based on metric type
                if 'systolic' in metric_name or 'diastolic' in metric_name:
                    display_value = f"{value:.0f} mmHg"
                    display_baseline = f"{mean_val:.0f} mmHg"
                elif 'hr' in metric_name or 'heart' in metric_name:
                    display_value = f"{value:.0f} bpm"
                    display_baseline = f"{mean_val:.0f} bpm"
                elif 'sleep' in metric_name:
                    display_value = f"{value:.1f} hours"
                    display_baseline = f"{mean_val:.1f} hours"
                elif 'step' in metric_name:
                    display_value = f"{value:.0f} steps"
                    display_baseline = f"{mean_val:.0f} steps"
                elif 'spo2' in metric_name or 'oxygen' in metric_name:
                    display_value = f"{value:.0f}%"
                    display_baseline = f"{mean_val:.0f}%"
                elif 'temp' in metric_name:
                    display_value = f"{value:.1f}°C"
                    display_baseline = f"{mean_val:.1f}°C"
                else:
                    display_value = f"{value:.1f}"
                    display_baseline = f"{mean_val:.1f}"
                
                # Direction of deviation and severity
                severity_class = "text-red-600" if abs(deviation_pct) > 20 or outside_threshold else "text-amber-600"
                
                deviations_html += f"""
                <div class="bg-gray-50 p-3 rounded">
                    <p class="font-medium {severity_class}">
                        {metric_name} {direction} by {abs(deviation_pct):.1f}%
                        {" (outside normal threshold)" if outside_threshold else ""}
                    </p>
                    <p class="text-gray-600">Value: {display_value} (Baseline: {display_baseline})</p>
                </div>
                """
            
            deviations_html += """
                </div>
            </div>
            """
        
        deviations_html += """
        </div>
        """
        
        return deviations_html
