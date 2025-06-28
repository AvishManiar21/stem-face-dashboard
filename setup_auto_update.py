#!/usr/bin/env python3
"""
Setup automatic daily data updates using Windows Task Scheduler
"""

import os
import sys
import subprocess
from datetime import datetime, time
import xml.etree.ElementTree as ET

def create_task_xml(python_path, script_path, working_dir):
    """Create Windows Task Scheduler XML configuration"""
    
    task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.now().isoformat()}</Date>
    <Author>STEM Face Dashboard</Author>
    <Description>Automatically update tutor data daily for AI predictions</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{datetime.now().replace(hour=6, minute=0, second=0, microsecond=0).isoformat()}</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{working_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""
    
    return task_xml

def setup_windows_task():
    """Setup Windows Task Scheduler task"""
    print("=== SETTING UP AUTOMATIC DAILY UPDATES ===")
    
    # Get paths
    python_path = sys.executable
    script_path = os.path.abspath("daily_data_updater.py")
    working_dir = os.path.dirname(script_path)
    task_name = "STEM_Face_Dashboard_Daily_Update"
    
    print(f"Python path: {python_path}")
    print(f"Script path: {script_path}")
    print(f"Working directory: {working_dir}")
    
    # Create XML file
    xml_content = create_task_xml(python_path, script_path, working_dir)
    xml_file = "task_schedule.xml"
    
    with open(xml_file, 'w', encoding='utf-16') as f:
        f.write(xml_content)
    
    print(f"Created task XML: {xml_file}")
    
    try:
        # Delete existing task if it exists
        subprocess.run([
            "schtasks", "/delete", "/tn", task_name, "/f"
        ], capture_output=True, check=False)
        
        # Create new task
        result = subprocess.run([
            "schtasks", "/create", "/xml", xml_file, "/tn", task_name
        ], capture_output=True, text=True, check=True)
        
        print("Windows Task Scheduler task created successfully!")
        print(f"Task name: {task_name}")
        print("Schedule: Daily at 6:00 AM")
        
        # Clean up XML file
        os.remove(xml_file)
        
        # Test the task
        print("\nTesting the scheduled task...")
        test_result = subprocess.run([
            "schtasks", "/run", "/tn", task_name
        ], capture_output=True, text=True)
        
        if test_result.returncode == 0:
            print("Task test successful!")
        else:
            print(f"Task test failed: {test_result.stderr}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating task: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def create_batch_file():
    """Create a batch file for manual execution"""
    batch_content = f"""@echo off
cd /d "{os.getcwd()}"
"{sys.executable}" daily_data_updater.py
pause
"""
    
    with open("run_daily_update.bat", 'w') as f:
        f.write(batch_content)
    
    print("Created run_daily_update.bat for manual execution")

def setup_alternative_scheduler():
    """Setup alternative scheduling using Python's schedule library"""
    print("\n=== SETTING UP ALTERNATIVE PYTHON SCHEDULER ===")
    
    scheduler_script = """#!/usr/bin/env python3
\"\"\"
Alternative scheduler using Python schedule library
Run this script to keep the scheduler running
\"\"\"

import schedule
import time
import subprocess
import sys
import os
from datetime import datetime

def run_daily_update():
    \"\"\"Run the daily update script\"\"\"
    print(f"Running daily update at {datetime.now()}")
    try:
        result = subprocess.run([
            sys.executable, 
            "daily_data_updater.py"
        ], cwd=os.getcwd(), capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Daily update completed successfully")
        else:
            print(f"Daily update failed: {result.stderr}")
            
    except Exception as e:
        print(f"Error running daily update: {e}")

# Schedule the task
schedule.every().day.at("06:00").do(run_daily_update)
schedule.every().day.at("18:00").do(run_daily_update)  # Backup evening run

print("Scheduler started - Daily updates at 6:00 AM and 6:00 PM")
print("Press Ctrl+C to stop")

try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
except KeyboardInterrupt:
    print("\\nScheduler stopped")
"""
    
    with open("python_scheduler.py", 'w') as f:
        f.write(scheduler_script)
    
    print("Created python_scheduler.py")
    print("   Run 'python python_scheduler.py' to start the Python-based scheduler")

def main():
    """Main setup function"""
    print("STEM Face Dashboard - Automatic Update Setup")
    print("=" * 50)
    
    # Test the daily updater first
    print("Testing daily updater...")
    try:
        from daily_data_updater import DailyDataUpdater
        updater = DailyDataUpdater()
        updater.analyze_existing_patterns()
        print("Daily updater is working correctly")
    except Exception as e:
        print(f"Error with daily updater: {e}")
        return
    
    # Create batch file for manual runs
    create_batch_file()
    
    # Try to setup Windows Task Scheduler
    if setup_windows_task():
        print("\nAUTOMATIC UPDATES CONFIGURED!")
        print("Your dashboard will now update daily at 6:00 AM")
    else:
        print("\nWindows Task Scheduler setup failed")
        print("Setting up alternative Python scheduler...")
        setup_alternative_scheduler()
    
    print("\nSETUP SUMMARY:")
    print("- Dataset updated with current dates")
    print("- Daily data updater created")
    print("- Automatic scheduling configured")
    print("- Manual run batch file created")
    
    print("\nMANUAL CONTROLS:")
    print("• Run daily update now: python daily_data_updater.py")
    print("• Backfill missing days: python daily_data_updater.py backfill 7")
    print("• Analyze patterns: python daily_data_updater.py analyze")
    print("• Manual update: run_daily_update.bat")
    
    print("\nAI STATUS:")
    print("Your AI will now have fresh data every day!")
    print("KPI cards will show current month data correctly.")

if __name__ == "__main__":
    main()