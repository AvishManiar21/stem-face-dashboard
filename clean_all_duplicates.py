#!/usr/bin/env python3
"""
Aggressively clean all duplicate sessions from face log data
Removes sessions where same tutor has multiple check-ins within 30 minutes
"""

import pandas as pd
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_all_duplicates():
    """Clean all duplicate sessions aggressively"""
    try:
        # Load the data
        df = pd.read_csv('logs/face_log_with_expected.csv')
        logger.info(f"Loaded {len(df)} total records")
        
        # Convert check_in to datetime
        df['check_in'] = pd.to_datetime(df['check_in'])
        df['check_out'] = pd.to_datetime(df['check_out'], errors='coerce')
        
        # Sort by tutor_id and check_in
        df = df.sort_values(['tutor_id', 'check_in'])
        
        # Create a copy for cleaning
        df_cleaned = df.copy()
        
        # Method 1: Remove exact duplicates (same tutor_id, check_in, check_out)
        initial_count = len(df_cleaned)
        df_cleaned = df_cleaned.drop_duplicates(subset=['tutor_id', 'check_in', 'check_out'])
        exact_dupes = initial_count - len(df_cleaned)
        logger.info(f"Removed {exact_dupes} exact duplicates")
        
        # Method 2: Remove duplicates where same tutor has multiple sessions within 30 minutes
        # Group by tutor and find sessions within 30 minutes
        df_cleaned = df_cleaned.sort_values(['tutor_id', 'check_in'])
        to_remove = set()
        
        for tutor_id in df_cleaned['tutor_id'].unique():
            tutor_sessions = df_cleaned[df_cleaned['tutor_id'] == tutor_id].copy()
            tutor_sessions = tutor_sessions.sort_values('check_in')
            
            for i in range(len(tutor_sessions)):
                if i in to_remove:
                    continue
                    
                current_session = tutor_sessions.iloc[i]
                current_time = current_session['check_in']
                
                # Check next sessions within 30 minutes
                for j in range(i + 1, len(tutor_sessions)):
                    if j in to_remove:
                        continue
                        
                    next_session = tutor_sessions.iloc[j]
                    next_time = next_session['check_in']
                    
                    # If within 30 minutes, keep the one with longer shift hours
                    if (next_time - current_time).total_seconds() <= 1800:  # 30 minutes
                        if current_session['shift_hours'] >= next_session['shift_hours']:
                            to_remove.add(tutor_sessions.index[j])
                        else:
                            to_remove.add(tutor_sessions.index[i])
                            break
                    else:
                        break
        
        # Remove the identified duplicates
        df_cleaned = df_cleaned.drop(index=list(to_remove))
        logger.info(f"Removed {len(to_remove)} sessions within 30 minutes of each other")
        
        # Method 3: Remove sessions where same tutor has multiple sessions on same day with overlapping times
        df_cleaned['date'] = df_cleaned['check_in'].dt.date
        to_remove_overlap = set()
        
        for date in df_cleaned['date'].unique():
            day_sessions = df_cleaned[df_cleaned['date'] == date].copy()
            
            for tutor_id in day_sessions['tutor_id'].unique():
                tutor_day_sessions = day_sessions[day_sessions['tutor_id'] == tutor_id].copy()
                tutor_day_sessions = tutor_day_sessions.sort_values('check_in')
                
                if len(tutor_day_sessions) > 1:
                    # Keep only the session with longest duration
                    longest_session_idx = tutor_day_sessions['shift_hours'].idxmax()
                    for idx in tutor_day_sessions.index:
                        if idx != longest_session_idx:
                            to_remove_overlap.add(idx)
        
        df_cleaned = df_cleaned.drop(index=list(to_remove_overlap))
        logger.info(f"Removed {len(to_remove_overlap)} overlapping sessions on same day")
        
        # Final statistics
        logger.info(f"Final count: {len(df_cleaned)} records (removed {len(df) - len(df_cleaned)} total)")
        
        # Show daily counts
        df_cleaned['date'] = df_cleaned['check_in'].dt.date
        daily_counts = df_cleaned.groupby('date').size().sort_values(ascending=False)
        logger.info(f"Top 5 days after cleaning: {daily_counts.head().to_dict()}")
        
        # Save cleaned data
        df_cleaned = df_cleaned.drop('date', axis=1)  # Remove temporary column
        df_cleaned.to_csv('logs/face_log_with_expected.csv', index=False)
        logger.info("Cleaned data saved successfully")
        
    except Exception as e:
        logger.error(f"Error cleaning duplicates: {e}")

if __name__ == "__main__":
    clean_all_duplicates()
