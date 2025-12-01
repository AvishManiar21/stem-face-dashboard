/**
 * Scheduling System Frontend
 * Phase 3: Frontend Development
 * Handles schedule grid, booking interface, and appointment management
 */

class SchedulingSystem {
    constructor() {
        this.currentWeekStart = this.getWeekStart(new Date());
        this.selectedTutors = [];
        this.weekData = null;
    }

    /**
     * Get the start of the week (Sunday) for a given date
     */
    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        const diff = d.getDate() - day; // Adjust to Sunday
        return new Date(d.setDate(diff));
    }

    /**
     * Format date as YYYY-MM-DD
     */
    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    /**
     * Load weekly schedule grid
     */
    async loadWeekSchedule(startDate = null) {
        try {
            if (!startDate) {
                startDate = this.formatDate(this.currentWeekStart);
            }

            const tutorIds = this.selectedTutors.length > 0 
                ? this.selectedTutors.join(',') 
                : null;

            let url = `/api/schedule/week?start_date=${startDate}`;
            if (tutorIds) {
                url += `&tutor_ids=${tutorIds}`;
            }

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.weekData = data;
            return data;
        } catch (error) {
            console.error('Error loading week schedule:', error);
            throw error;
        }
    }

    /**
     * Get available slots for a tutor on a specific date
     */
    async getAvailableSlots(tutorId, date, durationHours = 1) {
        try {
            const response = await fetch(
                `/api/schedule/available-slots?tutor_id=${tutorId}&date=${date}&duration=${durationHours}`
            );
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.available_slots || [];
        } catch (error) {
            console.error('Error getting available slots:', error);
            throw error;
        }
    }

    /**
     * Book an appointment
     */
    async bookAppointment(bookingData) {
        try {
            const response = await fetch('/api/appointments/book', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bookingData)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error booking appointment:', error);
            throw error;
        }
    }

    /**
     * Cancel an appointment
     */
    async cancelAppointment(appointmentId) {
        try {
            const response = await fetch('/api/appointments/cancel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ appointment_id: appointmentId })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error cancelling appointment:', error);
            throw error;
        }
    }

    /**
     * Get student's appointments
     */
    async getMyAppointments(studentEmail, upcomingOnly = true) {
        try {
            const response = await fetch(
                `/api/appointments/my-appointments?student_email=${encodeURIComponent(studentEmail)}&upcoming_only=${upcomingOnly}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.appointments || [];
        } catch (error) {
            console.error('Error getting appointments:', error);
            throw error;
        }
    }

    /**
     * Render weekly schedule grid
     */
    renderWeekGrid(containerId, weekData) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        if (!weekData || !weekData.tutors || !weekData.dates) {
            container.innerHTML = '<div class="alert alert-info">No schedule data available</div>';
            return;
        }

        const tutors = weekData.tutors || [];
        const dates = weekData.dates || [];
        const hours = weekData.hours || [];

        let html = `
            <div class="schedule-grid-container">
        `;

        // Create a separate grid for each day (Sunday to Friday)
        dates.forEach((date, dateIndex) => {
            const dateObj = new Date(date + 'T00:00:00');
            const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
            const dayNum = dateObj.getDate();
            const month = dateObj.toLocaleDateString('en-US', { month: 'short' });
            
            html += `
                <div class="day-schedule-grid">
                    <div class="day-schedule-header">
                        <div class="day-schedule-title">${month} ${dayNum}: ${dayName}</div>
                        <div class="day-schedule-time-slots">
            `;

            // Time slot headers (1:00 PM to 8:00 PM)
            // Add empty spacer for tutor column alignment
            html += `<div class="day-time-header-spacer"></div>`;
            
            hours.forEach(hour => {
                // Convert 24-hour to 12-hour format
                const hourNum = parseInt(hour.split(':')[0]);
                const period = hourNum >= 12 ? 'pm' : 'am';
                const displayHour = hourNum > 12 ? hourNum - 12 : (hourNum === 0 ? 12 : hourNum);
                const timeLabel = `${displayHour}:00 ${period}`;
                
                html += `
                    <div class="day-time-header">${timeLabel}</div>
                `;
            });

            html += `
                        </div>
                    </div>
                    <div class="day-schedule-body">
            `;

            // For each tutor, create a row for this day (only if they work on this day)
            tutors.forEach(tutor => {
                // Check if tutor has availability for this specific day
                const hasSlotsForDay = tutor.slots && tutor.slots[date] && Object.keys(tutor.slots[date]).length > 0;
                
                // Skip tutor if they don't work on this day
                if (!hasSlotsForDay) {
                    return; // Continue to next tutor
                }
                
                const tutorName = tutor.tutor_name || tutor.tutor_id;
                // Get first and last initial (matching image format: "Avish M.", "Bailey H.", etc.)
                let displayName = tutor.tutor_id;
                if (tutorName && tutorName !== tutor.tutor_id) {
                    const nameParts = tutorName.split(' ');
                    if (nameParts.length >= 2) {
                        displayName = `${nameParts[0]} ${nameParts[nameParts.length - 1].charAt(0)}.`;
                    } else {
                        displayName = nameParts[0];
                    }
                }

                html += `<div class="day-tutor-row">`;
                html += `
                    <div class="day-tutor-name">
                        ${displayName}
                        <i class="bi bi-pencil-square tutor-edit-icon" style="font-size: 0.75rem; opacity: 0.6; margin-left: 0.25rem;"></i>
                    </div>
                `;

                // Time slots for this tutor on this day
                hours.forEach(hour => {
                    const slotStatus = tutor.slots?.[date]?.[hour] || 'unavailable';
                    const slotClass = `day-schedule-slot day-schedule-slot-${slotStatus}`;
                    const slotTitle = `${tutorName} - ${date} ${hour} - ${slotStatus}`;
                    
                    html += `
                        <div class="${slotClass}" 
                             data-tutor-id="${tutor.tutor_id}"
                             data-tutor-name="${tutorName}"
                             data-date="${date}"
                             data-hour="${hour}"
                             title="${slotTitle}">
                        </div>
                    `;
                });

                html += `</div>`;
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += `</div>`;

        container.innerHTML = html;
        
        // Add week-view class for horizontal scrolling
        container.classList.add('week-view');

        // Add click handlers for available slots
        container.querySelectorAll('.schedule-slot-available, .day-schedule-slot-available').forEach(slot => {
            slot.addEventListener('click', () => {
                this.handleSlotClick(slot);
            });
        });
    }

    /**
     * Handle slot click for booking
     */
    handleSlotClick(slotElement) {
        const tutorId = slotElement.dataset.tutorId;
        const tutorName = slotElement.dataset.tutorName;
        const date = slotElement.dataset.date;
        const hour = slotElement.dataset.hour;

        // Open booking modal
        this.openBookingModal(tutorId, tutorName, date, hour);
    }

    /**
     * Open booking modal
     */
    openBookingModal(tutorId, tutorName, date, hour) {
        const modal = document.getElementById('bookingModal');
        if (modal) {
            // Set form values
            document.getElementById('bookingTutorId').value = tutorId;
            document.getElementById('bookingDate').value = date;
            
            // Set start time (convert hour format from "08:00" to "08:00:00" for time input)
            const startTime = hour.includes(':') ? hour : `${hour}:00`;
            document.getElementById('bookingStartTime').value = startTime;
            
            // Set default end time (1 hour later)
            const [hours, minutes] = startTime.split(':');
            const endHour = (parseInt(hours) + 1) % 24;
            const endTime = `${endHour.toString().padStart(2, '0')}:${minutes || '00'}`;
            document.getElementById('bookingEndTime').value = endTime;
            
            // Update modal title with tutor name
            const modalTitle = document.getElementById('bookingModalLabel');
            if (modalTitle) {
                modalTitle.innerHTML = `<i class="bi bi-calendar-plus"></i> Book Appointment with ${tutorName || tutorId}`;
            }
            
            // Show modal (Bootstrap 5)
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            console.warn('Booking modal not found');
        }
    }

    /**
     * Navigate to previous week
     */
    previousWeek() {
        const newDate = new Date(this.currentWeekStart);
        newDate.setDate(newDate.getDate() - 7);
        this.currentWeekStart = this.getWeekStart(newDate);
        this.loadAndRenderWeek();
    }

    /**
     * Navigate to next week
     */
    nextWeek() {
        const newDate = new Date(this.currentWeekStart);
        newDate.setDate(newDate.getDate() + 7);
        this.currentWeekStart = this.getWeekStart(newDate);
        this.loadAndRenderWeek();
    }

    /**
     * Navigate to current week
     */
    goToCurrentWeek() {
        this.currentWeekStart = this.getWeekStart(new Date());
        this.loadAndRenderWeek();
    }

    /**
     * Load and render week schedule
     */
    async loadAndRenderWeek() {
        try {
            const data = await this.loadWeekSchedule(this.formatDate(this.currentWeekStart));
            this.renderWeekGrid('scheduleGridContainer', data);
            
            // Update week display if function exists
            if (typeof updateWeekDisplay === 'function') {
                updateWeekDisplay();
            }
        } catch (error) {
            console.error('Error loading week:', error);
            const container = document.getElementById('scheduleGridContainer');
            if (container) {
                container.innerHTML = `
                    <div class="alert alert-danger">
                        <h5><i class="bi bi-exclamation-triangle"></i> Error Loading Schedule</h5>
                        <p>${error.message || 'Unknown error occurred'}</p>
                        <button class="btn btn-sm btn-outline-danger mt-2" onclick="window.schedulingSystem.loadAndRenderWeek()">
                            <i class="bi bi-arrow-clockwise"></i> Retry
                        </button>
                    </div>
                `;
            }
        }
    }
}

// Initialize global scheduling system instance
window.schedulingSystem = new SchedulingSystem();

