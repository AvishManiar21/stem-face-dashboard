#!/usr/bin/env python3
"""
Test script to verify calendar functionality works properly
"""

import requests
from datetime import datetime

def test_calendar_endpoint():
    """Test the calendar endpoint"""
    print("Testing calendar endpoint...")
    print("=" * 50)
    
    # Test current month
    try:
        response = requests.get('http://localhost:5000/calendar')
        
        if response.status_code == 200:
            print("✅ Calendar endpoint: SUCCESS")
            print(f"   Status Code: {response.status_code}")
            
            # Check if the response contains calendar data
            if 'calendar' in response.text.lower():
                print("   ✅ Calendar template loaded successfully")
            else:
                print("   ⚠️  Calendar template may not be loading properly")
                
        else:
            print(f"❌ Calendar endpoint: ERROR - HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Calendar endpoint: ERROR - {str(e)}")

def test_calendar_with_params():
    """Test calendar with specific year/month parameters"""
    print("\nTesting calendar with parameters...")
    print("=" * 50)
    
    # Test with current year/month
    now = datetime.now()
    year = now.year
    month = now.month
    
    try:
        response = requests.get(f'http://localhost:5000/calendar?year={year}&month={month}')
        
        if response.status_code == 200:
            print(f"✅ Calendar with parameters ({year}/{month}): SUCCESS")
            
            # Check for specific calendar elements
            if 'calendar-grid' in response.text:
                print("   ✅ Calendar grid found")
            if 'calendar-day' in response.text:
                print("   ✅ Calendar days found")
            if 'calendar-nav' in response.text:
                print("   ✅ Calendar navigation found")
                
        else:
            print(f"❌ Calendar with parameters: ERROR - HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Calendar with parameters: ERROR - {str(e)}")

def test_calendar_analytics():
    """Test the analytics calendar data generation"""
    print("\nTesting calendar analytics...")
    print("=" * 50)
    
    try:
        from analytics import TutorAnalytics
        
        # Initialize analytics
        analytics = TutorAnalytics()
        
        # Get current month data
        now = datetime.now()
        calendar_data = analytics.get_calendar_data(now.year, now.month)
        
        if calendar_data:
            print("✅ Calendar analytics: SUCCESS")
            print(f"   Year: {calendar_data.get('year')}")
            print(f"   Month: {calendar_data.get('month')}")
            print(f"   Month Name: {calendar_data.get('month_name')}")
            print(f"   Total Days: {calendar_data.get('summary', {}).get('total_days', 0)}")
            print(f"   Active Days: {calendar_data.get('summary', {}).get('active_days', 0)}")
            print(f"   Total Hours: {calendar_data.get('summary', {}).get('total_hours', 0)}")
            
            # Check calendar data structure
            calendar_days = calendar_data.get('calendar_data', {})
            if calendar_days:
                print(f"   Calendar Days: {len(calendar_days)} days with data")
            else:
                print("   ⚠️  No calendar days data found")
                
        else:
            print("❌ Calendar analytics: ERROR - No data returned")
            
    except Exception as e:
        print(f"❌ Calendar analytics: ERROR - {str(e)}")

def main():
    print("Testing Calendar Functionality")
    print("=" * 60)
    
    test_calendar_endpoint()
    test_calendar_with_params()
    test_calendar_analytics()
    
    print("\n" + "=" * 60)
    print("Calendar testing completed!")

if __name__ == "__main__":
    main() 