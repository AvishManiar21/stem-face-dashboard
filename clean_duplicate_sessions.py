#!/usr/bin/env python3
"""
Clean duplicate sessions from face log data
Removes sessions with same tutor_id and check_in but keeps the one with longer shift_hours
"""

import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_duplicate_sessions():
    """Clean duplicate sessions from the face log data"""
    try:
        # Load the data
        df = pd.read_csv('logs/face_log_with_expected.csv')
        logger.info(f"Loaded {len(df)} total records")
        
        # Convert check_in to datetime for proper sorting
        df['check_in'] = pd.to_datetime(df['check_in'])
        
        # Find duplicates based on tutor_id and check_in
        duplicates = df[df.duplicated(subset=['tutor_id', 'check_in'], keep=False)]
        logger.info(f"Found {len(duplicates)} duplicate records")
        
        if len(duplicates) > 0:
            # Group by tutor_id and check_in, keep the record with maximum shift_hours
            df_cleaned = df.sort_values(['tutor_id', 'check_in', 'shift_hours'], ascending=[True, True, False])
            df_cleaned = df_cleaned.drop_duplicates(subset=['tutor_id', 'check_in'], keep='first')
            
            logger.info(f"After cleaning: {len(df_cleaned)} records (removed {len(df) - len(df_cleaned)} duplicates)")
            
            # Save the cleaned data
            df_cleaned.to_csv('logs/face_log_with_expected.csv', index=False)
            logger.info("Cleaned data saved successfully")
            
            # Show some statistics
            df_cleaned['date'] = df_cleaned['check_in'].dt.date
            daily_counts = df_cleaned.groupby('date').size().sort_values(ascending=False)
            logger.info(f"Top 5 days after cleaning: {daily_counts.head().to_dict()}")
            
        else:
            logger.info("No duplicates found")
            
    except Exception as e:
        logger.error(f"Error cleaning duplicates: {e}")

if __name__ == "__main__":
    clean_duplicate_sessions()
