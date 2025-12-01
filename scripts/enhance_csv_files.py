"""
Phase 1: Data Structure Updates
Enhance CSV files for scheduling system
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

# Path to data directory
DATA_DIR = Path('data/core')

def enhance_appointments_csv():
    """Add booking_type and confirmation_status columns to appointments.csv"""
    print("Enhancing appointments.csv...")
    
    df = pd.read_csv(DATA_DIR / 'appointments.csv')
    
    # Add new columns with default values
    if 'booking_type' not in df.columns:
        # Set default based on existing data
        # For existing appointments, assume they were admin scheduled
        df['booking_type'] = 'admin_scheduled'
        print("  ✓ Added 'booking_type' column (default: admin_scheduled)")
    
    if 'confirmation_status' not in df.columns:
        # Map existing status to confirmation_status
        status_mapping = {
            'scheduled': 'confirmed',
            'completed': 'confirmed',
            'cancelled': 'cancelled',
            'no-show': 'confirmed'  # They were confirmed but didn't show
        }
        df['confirmation_status'] = df['status'].map(status_mapping).fillna('pending')
        print("  ✓ Added 'confirmation_status' column (mapped from status)")
    
    # Reorder columns to put new fields after status
    columns_order = [
        'appointment_id', 'tutor_id', 'student_name', 'student_email', 
        'course_id', 'appointment_date', 'start_time', 'end_time', 
        'status', 'booking_type', 'confirmation_status', 'notes', 
        'created_at', 'updated_at'
    ]
    
    # Only reorder if all columns exist
    if all(col in df.columns for col in columns_order):
        df = df[columns_order]
    
    # Save back to CSV
    df.to_csv(DATA_DIR / 'appointments.csv', index=False)
    print(f"  ✓ Updated appointments.csv ({len(df)} rows)")
    return df

def enhance_availability_csv():
    """Add slot_status column to availability.csv"""
    print("\nEnhancing availability.csv...")
    
    df = pd.read_csv(DATA_DIR / 'availability.csv')
    
    # Add slot_status column
    if 'slot_status' not in df.columns:
        # Default all existing availability to 'available'
        df['slot_status'] = 'available'
        print("  ✓ Added 'slot_status' column (default: available)")
    
    # Save back to CSV
    df.to_csv(DATA_DIR / 'availability.csv', index=False)
    print(f"  ✓ Updated availability.csv ({len(df)} rows)")
    return df

def create_time_slots_csv():
    """Create time_slots.csv for granular time slot management"""
    print("\nCreating time_slots.csv...")
    
    slots_file = DATA_DIR / 'time_slots.csv'
    
    if slots_file.exists():
        print("  ⚠ time_slots.csv already exists, skipping creation")
        return pd.read_csv(slots_file)
    
    # Create empty DataFrame with required columns
    columns = ['slot_id', 'date', 'start_time', 'end_time', 'tutor_id', 'status', 'appointment_id']
    df = pd.DataFrame(columns=columns)
    
    # Save empty CSV
    df.to_csv(slots_file, index=False)
    print("  ✓ Created time_slots.csv (empty, will be populated by scheduling system)")
    return df

def main():
    """Run all enhancements"""
    print("=" * 60)
    print("Phase 1: Data Structure Updates")
    print("=" * 60)
    
    try:
        # Enhance appointments.csv
        appointments_df = enhance_appointments_csv()
        
        # Enhance availability.csv
        availability_df = enhance_availability_csv()
        
        # Create time_slots.csv
        time_slots_df = create_time_slots_csv()
        
        print("\n" + "=" * 60)
        print("Phase 1 Complete!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  - appointments.csv: {len(appointments_df)} rows, {len(appointments_df.columns)} columns")
        print(f"  - availability.csv: {len(availability_df)} rows, {len(availability_df.columns)} columns")
        print(f"  - time_slots.csv: {len(time_slots_df)} rows, {len(time_slots_df.columns)} columns")
        print("\nNew fields added:")
        print("  - appointments.csv: booking_type, confirmation_status")
        print("  - availability.csv: slot_status")
        print("  - time_slots.csv: Created (empty)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())

