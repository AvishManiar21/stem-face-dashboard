#!/usr/bin/env python3
"""
Test script to verify all chart types are working properly
"""

import requests
import json

# Test all chart types
chart_types = [
    'checkins_per_tutor',
    'hours_per_tutor', 
    'avg_session_duration_per_tutor',
    'tutor_consistency_score',
    'daily_checkins',
    'daily_hours',
    'hourly_checkins_dist',
    'monthly_hours',
    'avg_hours_per_day_of_week',
    'checkins_per_day_of_week',
    'cumulative_checkins',
    'cumulative_hours',
    'hourly_activity_by_day',
    'punctuality_analysis',
    'session_duration_distribution'
]

def test_chart_type(chart_type):
    """Test a specific chart type"""
    print(f"\nTesting chart type: {chart_type}")
    
    # Prepare the request data
    data = {
        'chartKey': chart_type,
        'tutor_ids': '',
        'start_date': '',
        'end_date': '',
        'duration': '',
        'day_type': '',
        'shift_start_hour': 0,
        'shift_end_hour': 23
    }
    
    try:
        # Make the request
        response = requests.post('http://localhost:5000/chart-data', 
                               json=data, 
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if the chart data exists
            if chart_type in result:
                chart_data = result[chart_type]
                if isinstance(chart_data, dict) and len(chart_data) > 0:
                    print(f"✅ {chart_type}: SUCCESS - {len(chart_data)} data points")
                    print(f"   Sample data: {dict(list(chart_data.items())[:3])}")
                else:
                    print(f"⚠️  {chart_type}: WARNING - Empty data")
            else:
                print(f"❌ {chart_type}: ERROR - Chart data not found in response")
                
        else:
            print(f"❌ {chart_type}: ERROR - HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ {chart_type}: ERROR - {str(e)}")

def main():
    print("Testing all chart types...")
    print("=" * 50)
    
    for chart_type in chart_types:
        test_chart_type(chart_type)
    
    print("\n" + "=" * 50)
    print("Chart testing completed!")

if __name__ == "__main__":
    main() 