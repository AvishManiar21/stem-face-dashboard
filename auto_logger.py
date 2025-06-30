#!/usr/bin/env python3
"""
Auto-logger script that automatically adds current day logs
to simulate real-time tutor check-ins and check-outs
"""

import pandas as pd
import random
import time
import threading
from datetime import datetime, timedelta
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoLogger:
    def __init__(self, log_file='logs/face_log.csv'):
        self.log_file = log_file
        self.tutors = [
            {'id': '2598056', 'name': 'Liam Johnson'},
            {'id': '6362733', 'name': 'Meera Nair'},
            {'id': '7644166', 'name': 'Ryan Scott'},
            {'id': '6403246', 'name': 'Isabella Davis'},
            {'id': '7916493', 'name': 'Arjun Kapoor'},
            {'id': '8853681', 'name': 'Aanya Mehta'},
            {'id': '4146623', 'name': 'Noah Wilson'},
            {'id': '2115580', 'name': 'Saanvi Joshi'},
            {'id': '2701634', 'name': 'Emily Brown'},
            {'id': '3534553', 'name': 'Benjamin Lewis'},
            {'id': '6887917', 'name': 'Lucas Moore'},
            {'id': '7134699', 'name': 'Vivaan Kumar'},
            {'id': '2750869', 'name': 'Neha Patel'},
            {'id': '6474141', 'name': 'Anaya Sharma'},
            {'id': '6664205', 'name': 'Mason Lee'},
            {'id': '2425166', 'name': 'Aarav Shah'},
            {'id': '2630571', 'name': 'Avni Desai'},
            {'id': '9323660', 'name': 'Zoya Singh'},
            {'id': '2192067', 'name': 'James Martin'},
            {'id': '7264805', 'name': 'Isha Reddy'}
        ]
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the auto-logger in a separate thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("Auto-logger started")
            
    def stop(self):
        """Stop the auto-logger"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Auto-logger stopped")
            
    def _run(self):
        """Main auto-logger loop"""
        while self.running:
            try:
                # Add a random check-in/check-out every 30-120 seconds
                self._add_random_log()
                time.sleep(random.randint(30, 120))
            except Exception as e:
                logger.error(f"Error in auto-logger: {e}")
                time.sleep(60)  # Wait a minute before retrying
                
    def _add_random_log(self):
        """Add a random check-in/check-out log for today, avoiding duplicates"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Load existing logs
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
        else:
            df = pd.DataFrame(columns=['tutor_id', 'tutor_name', 'check_in', 'check_out', 'shift_hours', 'snapshot_in', 'snapshot_out'])
        
        today_logs = df[df['check_in'].str.startswith(today, na=False)]
        existing_pairs = set(zip(today_logs['tutor_id'], today_logs['check_in']))
        
        # Select a random tutor
        tutor = random.choice(self.tutors)
        
        # Generate random check-in time (between 8 AM and 6 PM)
        hour = random.randint(8, 18)
        minute = random.randint(0, 59)
        check_in = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        check_in_str = check_in.strftime('%Y-%m-%d %H:%M')
        
        # Avoid duplicate for this tutor and check-in time
        if (tutor['id'], check_in_str) in existing_pairs:
            return
        
        # Generate check-out time (1-4 hours later)
        shift_hours = random.uniform(1.0, 4.0)
        check_out = check_in + timedelta(hours=shift_hours)
        
        # Create new log entry
        new_log = {
            'tutor_id': tutor['id'],
            'tutor_name': tutor['name'],
            'check_in': check_in_str,
            'check_out': check_out.strftime('%Y-%m-%d %H:%M'),
            'shift_hours': round(shift_hours, 2),
            'snapshot_in': f"snapshots/{tutor['id']}.jpg",
            'snapshot_out': f"snapshots/{tutor['id']}.jpg"
        }
        
        # Add to dataframe
        df = pd.concat([df, pd.DataFrame([new_log])], ignore_index=True)
        
        # Save to file
        df.to_csv(self.log_file, index=False)
        
        logger.info(f"Added auto-log: {tutor['name']} checked in at {check_in.strftime('%H:%M')} for {shift_hours:.1f} hours")
        
    def add_today_logs(self, count=5):
        """Add multiple logs for today at once, avoiding duplicates"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Load existing data
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
        else:
            df = pd.DataFrame(columns=['tutor_id', 'tutor_name', 'check_in', 'check_out', 'shift_hours', 'snapshot_in', 'snapshot_out'])
        
        today_logs = df[df['check_in'].str.startswith(today, na=False)]
        existing_pairs = set(zip(today_logs['tutor_id'], today_logs['check_in']))
        new_logs = []
        attempts = 0
        while len(new_logs) < count and attempts < count * 3:
            tutor = random.choice(self.tutors)
            hour = random.randint(8, 18)
            minute = random.randint(0, 59)
            check_in = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            check_in_str = check_in.strftime('%Y-%m-%d %H:%M')
            if (tutor['id'], check_in_str) in existing_pairs:
                attempts += 1
                continue
            shift_hours = random.uniform(1.0, 4.0)
            check_out = check_in + timedelta(hours=shift_hours)
            new_log = {
                'tutor_id': tutor['id'],
                'tutor_name': tutor['name'],
                'check_in': check_in_str,
                'check_out': check_out.strftime('%Y-%m-%d %H:%M'),
                'shift_hours': round(shift_hours, 2),
                'snapshot_in': f"snapshots/{tutor['id']}.jpg",
                'snapshot_out': f"snapshots/{tutor['id']}.jpg"
            }
            new_logs.append(new_log)
            existing_pairs.add((tutor['id'], check_in_str))
            attempts += 1
        if new_logs:
            df = pd.concat([df, pd.DataFrame(new_logs)], ignore_index=True)
            df.to_csv(self.log_file, index=False)
            logger.info(f"Added {len(new_logs)} today logs (no duplicates)")
        return new_logs

# Global auto-logger instance
auto_logger = AutoLogger()

def start_auto_logger():
    """Start the auto-logger"""
    auto_logger.start()
    
def stop_auto_logger():
    """Stop the auto-logger"""
    auto_logger.stop()
    
def add_today_logs(count=5):
    """Add today logs manually"""
    return auto_logger.add_today_logs(count)

if __name__ == "__main__":
    # Test the auto-logger
    print("Adding 5 today logs...")
    logs = add_today_logs(5)
    for log in logs:
        print(f"Added: {log['tutor_name']} - {log['check_in']} to {log['check_out']} ({log['shift_hours']} hours)") 