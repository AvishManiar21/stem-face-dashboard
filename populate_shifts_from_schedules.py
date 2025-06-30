#!/usr/bin/env python3
"""
Populate Shifts and Shift Assignments from Schedule Data
Converts expanded_schedules.csv into shifts.csv and shift_assignments.csv
for future use in the dashboard
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ShiftPopulator:
    def __init__(self):
        self.logs_dir = 'logs'
        self.schedule_file = os.path.join(self.logs_dir, 'expanded_schedules.csv')
        self.shifts_file = os.path.join(self.logs_dir, 'shifts.csv')
        self.assignments_file = os.path.join(self.logs_dir, 'shift_assignments.csv')
        
    def load_schedule_data(self):
        """Load the expanded schedule data"""
        if not os.path.exists(self.schedule_file):
            logger.error(f"Schedule file not found: {self.schedule_file}")
            return None
            
        try:
            df = pd.read_csv(self.schedule_file)
            logger.info(f"Loaded {len(df)} schedule entries")
            return df
        except Exception as e:
            logger.error(f"Error loading schedule data: {e}")
            return None
    
    def create_unique_shifts(self, schedule_df):
        """Create unique shifts from schedule data"""
        if schedule_df is None or schedule_df.empty:
            return pd.DataFrame()
            
        # Group by unique shift patterns (tutor, start_time, end_time)
        unique_shifts = schedule_df.groupby(['tutor_id', 'tutor_name', 'start_time', 'end_time']).first().reset_index()
        
        # Create shift_id for each unique pattern
        unique_shifts['shift_id'] = range(1, len(unique_shifts) + 1)
        unique_shifts['shift_name'] = unique_shifts.apply(
            lambda row: f"{row['tutor_name']} - {row['start_time']}-{row['end_time']}", 
            axis=1
        )
        
        # Select only the columns needed for shifts.csv
        shifts_df = unique_shifts[['shift_id', 'shift_name', 'start_time', 'end_time']].copy()
        
        logger.info(f"Created {len(shifts_df)} unique shifts")
        return shifts_df, unique_shifts
    
    def create_shift_assignments(self, schedule_df, days_ahead=365):
        """Create shift assignments for future dates based on existing schedule patterns"""
        if schedule_df.empty:
            return pd.DataFrame()
            
        assignments = []
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        # Group by tutor and time patterns to find recurring schedules
        schedule_patterns = schedule_df.groupby(['tutor_id', 'tutor_name', 'start_time', 'end_time']).agg({
            'date': lambda x: list(x)
        }).reset_index()
        
        assignment_id = 1
        
        for _, pattern in schedule_patterns.iterrows():
            dates = pattern['date']
            if not dates:
                continue
                
            # Convert dates to datetime objects
            date_objects = [datetime.strptime(date, '%Y-%m-%d').date() for date in dates if date]
            
            # Find recurring patterns (same day of week, same time)
            if len(date_objects) >= 2:
                # Sort dates to find patterns
                date_objects.sort()
                
                # Find the most common day of week for this pattern
                weekdays = [date.weekday() for date in date_objects]
                from collections import Counter
                most_common_weekday = Counter(weekdays).most_common(1)[0][0]
                
                # Generate future assignments for this pattern
                current_date = today
                while current_date <= end_date:
                    if current_date.weekday() == most_common_weekday:
                        assignment = {
                            'assignment_id': assignment_id,
                            'shift_id': None,  # Will be set later
                            'tutor_id': pattern['tutor_id'],
                            'tutor_name': pattern['tutor_name'],
                            'date': current_date.strftime('%Y-%m-%d'),
                            'day_name': current_date.strftime('%A'),
                            'start_time': pattern['start_time'],
                            'end_time': pattern['end_time'],
                            'status': 'scheduled'
                        }
                        assignments.append(assignment)
                        assignment_id += 1
                    
                    current_date += timedelta(days=1)
        
        assignments_df = pd.DataFrame(assignments)
        # Ensure columns exist
        required_cols = ['assignment_id', 'tutor_id', 'tutor_name', 'date', 'day_name', 'start_time', 'end_time', 'status', 'shift_id']
        for col in required_cols:
            if col not in assignments_df.columns:
                assignments_df[col] = None
        logger.info(f"Created {len(assignments_df)} shift assignments for the next {days_ahead} days. Columns: {list(assignments_df.columns)}")
        return assignments_df
    
    def link_assignments_to_shifts(self, assignments_df, shifts_df):
        """Link assignments to their corresponding shifts"""
        if assignments_df.empty or shifts_df.empty:
            logger.warning("Assignments or shifts DataFrame is empty!")
            return assignments_df
        
        # Debug: print columns
        logger.info(f"Assignments columns: {list(assignments_df.columns)}")
        logger.info(f"Shifts columns: {list(shifts_df.columns)}")
        
        # Create a mapping from (tutor_id, start_time, end_time) to shift_id
        shift_mapping = {}
        time_mapping = {}
        for _, shift in shifts_df.iterrows():
            key = (shift.get('tutor_id'), shift['start_time'], shift['end_time'])
            shift_mapping[key] = shift['shift_id']
            time_key = (shift['start_time'], shift['end_time'])
            time_mapping[time_key] = shift['shift_id']
        
        unmatched = []
        # Update assignments with shift_id
        for idx, assignment in assignments_df.iterrows():
            key = (assignment.get('tutor_id'), assignment['start_time'], assignment['end_time'])
            time_key = (assignment['start_time'], assignment['end_time'])
            if key in shift_mapping:
                assignments_df.loc[idx, 'shift_id'] = shift_mapping[key]
            elif time_key in time_mapping:
                assignments_df.loc[idx, 'shift_id'] = time_mapping[time_key]
            else:
                unmatched.append(key)
        if unmatched:
            logger.warning(f"Unmatched assignments (showing up to 10): {unmatched[:10]}")
        return assignments_df
    
    def save_files(self, shifts_df, assignments_df):
        """Save the generated data to CSV files"""
        try:
            # Save shifts (add missing columns for backend compatibility)
            if not shifts_df.empty:
                shifts_df['active'] = True
                shifts_df['days_of_week'] = 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday'  # Default to all days
                shifts_df['created_by'] = 'system'
                shifts_df['created_at'] = datetime.now().isoformat()
                shifts_df.to_csv(self.shifts_file, index=False)
                logger.info(f"Saved {len(shifts_df)} shifts to {self.shifts_file}")
            
            # Save assignments (convert columns for backend compatibility)
            if not assignments_df.empty:
                assignments_df = assignments_df.rename(columns={
                    'date': 'start_date',
                })
                assignments_df['end_date'] = assignments_df['start_date']
                assignments_df['active'] = True
                assignments_df['assigned_by'] = 'system'
                assignments_df['assigned_at'] = datetime.now().isoformat()
                assignments_df.to_csv(self.assignments_file, index=False)
                logger.info(f"Saved {len(assignments_df)} shift assignments to {self.assignments_file}")
            
        except Exception as e:
            logger.error(f"Error saving files: {e}")
            raise
    
    def run(self, days_ahead=365):
        """Main execution method"""
        logger.info("Starting shift population from schedules...")
        
        # Load schedule data
        schedule_df = self.load_schedule_data()
        if schedule_df is None:
            return False
        
        # Create unique shifts
        shifts_df, unique_shifts = self.create_unique_shifts(schedule_df)
        if shifts_df.empty:
            logger.warning("No unique shifts found")
            return False
        
        # Create assignments
        assignments_df = self.create_shift_assignments(schedule_df, days_ahead)
        if assignments_df.empty:
            logger.warning("No assignments created")
            return False
        
        # Link assignments to shifts
        assignments_df = self.link_assignments_to_shifts(assignments_df, shifts_df)
        
        # Save files
        success = self.save_files(shifts_df, assignments_df)
        
        if success:
            logger.info("✅ Successfully populated shifts and assignments!")
            logger.info(f"📊 Summary:")
            logger.info(f"   - Unique shifts: {len(shifts_df)}")
            logger.info(f"   - Total assignments: {len(assignments_df)}")
            logger.info(f"   - Date range: {datetime.now().date()} to {(datetime.now().date() + timedelta(days=days_ahead))}")
        else:
            logger.error("❌ Failed to save files")
        
        return success

def main():
    """Main function for command line usage"""
    import sys
    
    # Parse command line arguments
    days_ahead = 365  # Default to 1 year
    if len(sys.argv) > 1:
        try:
            days_ahead = int(sys.argv[1])
        except ValueError:
            print("Usage: python populate_shifts_from_schedules.py [days_ahead]")
            print("  days_ahead: Number of days to generate assignments for (default: 365)")
            return
    
    # Run the populator
    populator = ShiftPopulator()
    success = populator.run(days_ahead)
    
    if success:
        print("\n🎉 Shift population completed successfully!")
        print("Your upcoming shifts should now display properly in the dashboard.")
    else:
        print("\n❌ Shift population failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 