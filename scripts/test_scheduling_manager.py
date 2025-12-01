"""Test script for SchedulingManager"""
from app.core.scheduling_manager import SchedulingManager
from datetime import datetime

print("Testing SchedulingManager...")
sm = SchedulingManager()

print(f"✓ Loaded {len(sm.appointments)} appointments")
print(f"✓ Loaded {len(sm.tutors)} tutors")

# Test week schedule
start_date = datetime.now().strftime('%Y-%m-%d')
result = sm.get_week_schedule(start_date)
print(f"✓ Week schedule: {len(result['tutors'])} tutors, {len(result['dates'])} dates, {len(result['hours'])} hours")

# Test available slots
if not sm.tutors.empty:
    tutor_id = sm.tutors.iloc[0]['tutor_id']
    date = '2025-12-01'
    slots = sm.get_available_slots(tutor_id, date)
    print(f"✓ Available slots for {tutor_id} on {date}: {len(slots)} slots")

# Test slot status
if not sm.tutors.empty:
    tutor_id = sm.tutors.iloc[0]['tutor_id']
    status = sm.get_slot_status(tutor_id, '2025-12-01', '13:00')
    print(f"✓ Slot status for {tutor_id} on 2025-12-01 at 13:00: {status}")

print("\n✓ All tests passed!")

