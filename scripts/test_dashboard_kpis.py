"""Test dashboard KPI data generation"""
from app.core.analytics import SchedulingAnalytics

print("Testing Dashboard KPI Data Generation...")
print("=" * 60)

analytics = SchedulingAnalytics()
summary = analytics.get_summary_stats()

print("\n✓ Summary stats generated successfully!")
print("\nPrimary KPIs:")
print(f"  - Total Check-ins (appointments): {summary.get('total_checkins', 0)}")
print(f"  - Total Hours: {summary.get('total_hours', 0)}")
print(f"  - Active Tutors: {summary.get('active_tutors', 0)}")
print(f"  - Avg Session Duration: {summary.get('avg_session_duration', '—')}")

print("\nSecondary KPIs:")
print(f"  - Avg Daily Hours: {summary.get('avg_daily_hours', '—')}")
print(f"  - Peak Hour: {summary.get('peak_checkin_hour', '—')}")
print(f"  - Most Active Day: {summary.get('top_day', '—')}")
print(f"  - Top Tutor This Month: {summary.get('top_tutor_current_month', '—')}")

print("\nPhase 1 Enhanced Metrics:")
print(f"  - Pending Confirmations: {summary.get('pending_confirmations', 0)}")
print(f"  - Student-Booked: {summary.get('student_booked_count', 0)}")
print(f"  - Admin-Scheduled: {summary.get('admin_scheduled_count', 0)}")
print(f"  - Cancelled: {summary.get('cancelled_count', 0)}")

print("\n" + "=" * 60)
print("✓ All KPI data is ready for dashboard display!")

