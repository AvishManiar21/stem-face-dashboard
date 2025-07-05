/**
 * Forecasting and AI Insights JavaScript Module
 * Handles all forecasting and AI-related frontend functionality
 */

class ForecastingManager {
    constructor() {
        this.forecastingData = null;
        this.aiInsights = null;
        this.charts = {};
        this.isInitialized = false;
    }

    /**
     * Initialize forecasting functionality
     */
    async initialize() {
        try {
            console.log('Initializing forecasting functionality...');
            
            // Load forecasting data
            await this.loadForecastingData();
            
            // Load AI insights
            await this.loadAIInsights();
            
            // Initialize charts
            this.initializeCharts();
            
            // Update UI
            this.updateForecastingUI();
            this.updateAIInsightsUI();
            
            this.isInitialized = true;
            console.log('Forecasting functionality initialized successfully');
            
        } catch (error) {
            console.error('Error initializing forecasting functionality:', error);
            this.showForecastingError();
        }
    }

    /**
     * Load forecasting data from API
     */
    async loadForecastingData() {
        try {
            console.log('Loading forecasting data...');
            const response = await fetch('/api/forecasting-data');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.forecastingData = await response.json();
            console.log('Forecasting data loaded:', this.forecastingData);
            
        } catch (error) {
            console.error('Error loading forecasting data:', error);
            this.forecastingData = null;
            throw error;
        }
    }

    /**
     * Load AI insights from API
     */
    async loadAIInsights() {
        try {
            console.log('Loading AI insights...');
            const response = await fetch('/api/ai-insights');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.aiInsights = await response.json();
            console.log('AI insights loaded:', this.aiInsights);
            
        } catch (error) {
            console.error('Error loading AI insights:', error);
            this.aiInsights = null;
            throw error;
        }
    }

    /**
     * Update forecasting UI elements
     */
    updateForecastingUI() {
        if (!this.forecastingData) {
            this.showForecastingError();
            return;
        }

        try {
            // Update next week prediction
            this.updateElement('nextWeekHours', this.forecastingData.next_week_hours);
            this.updateElement('nextWeekConfidence', this.forecastingData.next_week_confidence + '%');
            this.updateElement('nextWeekTrend', this.forecastingData.next_week_trend);
            this.updateElement('nextWeekCI', this.forecastingData.next_week_ci);
            this.updateElement('nextWeekMethods', this.forecastingData.next_week_methods);

            // Update next month prediction
            this.updateElement('nextMonthHours', this.forecastingData.next_month_hours);
            this.updateElement('nextMonthConfidence', this.forecastingData.next_month_confidence + '%');
            this.updateElement('nextMonthTrend', this.forecastingData.next_month_trend);
            this.updateElement('nextMonthCI', this.forecastingData.next_month_ci);

            // Update tutor demand
            this.updateElement('tutorDemandWeek', this.forecastingData.tutor_demand_week);
            this.updateElement('tutorDemandMonth', this.forecastingData.tutor_demand_month);

            // Update busiest patterns
            this.updateElement('busiestDay', this.forecastingData.busiest_day);
            this.updateElement('busiestHour', this.forecastingData.busiest_hour);

            // Update anomaly detection
            this.updateElement('anomalyStatus', this.forecastingData.anomaly_status);
            this.updateElement('anomalyPercent', this.forecastingData.anomaly_percent + '%');
            this.updateElement('anomalyLastWeek', this.forecastingData.anomaly_last_week + ' anomalies');
            this.updateElement('anomalyPrevAvg', this.forecastingData.anomaly_prev_avg + 'h avg');

            // Update historical comparison
            this.updateElement('histLastWeek', this.forecastingData.hist_last_week + 'h');
            this.updateElement('histForecastWeek', this.forecastingData.hist_forecast_week + 'h forecast');
            this.updateElement('histLastMonth', this.forecastingData.hist_last_month + 'h');
            this.updateElement('histForecastMonth', this.forecastingData.hist_forecast_month + 'h forecast');

            // Update last updated timestamp
            this.updateElement('forecastLastUpdated', this.forecastingData.forecast_last_updated);

            // Update hourly forecast table
            this.updateHourlyForecastTable();

            // Update scenario simulation
            this.updateScenarioSimulation();

        } catch (error) {
            console.error('Error updating forecasting UI:', error);
            this.showForecastingError();
        }
    }

    /**
     * Update AI insights UI elements
     */
    updateAIInsightsUI() {
        if (!this.aiInsights) {
            this.showAIInsightsError();
            return;
        }

        try {
            // Update AI confidence score
            this.updateElement('aiConfidenceScore', this.aiInsights.confidence_score + '%');

            // Update forecast accuracy
            this.updateElement('forecastAccuracy', this.aiInsights.forecast_accuracy + '%');

            // Update NLP summary
            this.updateNLPSummary();

            // Update AI recommendations
            this.updateAIRecommendations();

            // Update growth opportunities
            this.updateGrowthOpportunities();

        } catch (error) {
            console.error('Error updating AI insights UI:', error);
            this.showAIInsightsError();
        }
    }

    /**
     * Update NLP summary
     */
    updateNLPSummary() {
        const summaryElement = document.getElementById('improvedNLSummary');
        if (summaryElement && this.aiInsights.nlp_summary) {
            const spanElement = summaryElement.querySelector('span');
            if (spanElement) {
                spanElement.textContent = this.aiInsights.nlp_summary;
            }
        }
    }

    /**
     * Update AI recommendations
     */
    updateAIRecommendations() {
        const recommendationsElement = document.getElementById('aiRecommendations');
        if (!recommendationsElement) return;

        if (this.aiInsights.ai_recommendations && this.aiInsights.ai_recommendations.length > 0) {
            const recommendationsHtml = this.aiInsights.ai_recommendations.map(rec => `
                <div class="card mb-3 ${this.getRecommendationCardClass(rec.priority)}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="card-title mb-1">
                                    <i class="fas ${this.getRecommendationIcon(rec.type)} me-2"></i>
                                    ${rec.title}
                                </h6>
                                <p class="card-text small mb-2">${rec.description}</p>
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>Action:</strong> ${rec.action}
                                    </div>
                                    <div class="col-md-6">
                                        <strong>Impact:</strong> ${rec.impact}
                                    </div>
                                </div>
                            </div>
                            <span class="badge ${this.getPriorityBadgeClass(rec.priority)}">${rec.priority}</span>
                        </div>
                    </div>
                </div>
            `).join('');
            recommendationsElement.innerHTML = recommendationsHtml;
        } else {
            recommendationsElement.innerHTML = '<div class="text-muted">No recommendations available</div>';
        }
    }

    /**
     * Update growth opportunities
     */
    updateGrowthOpportunities() {
        const opportunitiesElement = document.getElementById('topGrowthOpportunities');
        if (!opportunitiesElement) return;

        if (this.aiInsights.growth_opportunities && this.aiInsights.growth_opportunities.length > 0) {
            const opportunitiesHtml = this.aiInsights.growth_opportunities.map(opp => 
                `<li class="mb-1"><i class="fas fa-arrow-up text-success me-1"></i>${opp}</li>`
            ).join('');
            opportunitiesElement.innerHTML = opportunitiesHtml;
        } else {
            opportunitiesElement.innerHTML = '<li class="text-muted">No specific opportunities identified</li>';
        }
    }

    /**
     * Update hourly forecast table
     */
    updateHourlyForecastTable() {
        const tableElement = document.getElementById('hourlyForecastTable');
        if (!tableElement || !this.forecastingData.hourly_forecast) return;

        const hourlyData = this.forecastingData.hourly_forecast;
        let tableHtml = `
            <table class="table table-sm table-striped">
                <thead>
                    <tr>
                        <th>Hour</th>
                        <th>Predicted Hours</th>
                        <th>Predicted Sessions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (let hour = 0; hour < 24; hour++) {
            const hourData = hourlyData[hour] || { predicted_hours: 0, predicted_sessions: 0 };
            tableHtml += `
                <tr>
                    <td>${hour.toString().padStart(2, '0')}:00</td>
                    <td>${hourData.predicted_hours}h</td>
                    <td>${hourData.predicted_sessions}</td>
                </tr>
            `;
        }

        tableHtml += '</tbody></table>';
        tableElement.innerHTML = tableHtml;
    }

    /**
     * Update scenario simulation
     */
    updateScenarioSimulation() {
        if (!this.forecastingData.scenario_simulation) return;

        const scenarios = this.forecastingData.scenario_simulation;
        
        this.updateElement('simTutors2', scenarios['+2_tutors'] ? scenarios['+2_tutors'] + 'h' : '-');
        this.updateElement('simTutors5', scenarios['+5_tutors'] ? scenarios['+5_tutors'] + 'h' : '-');
        this.updateElement('simTutors10', scenarios['+10_tutors'] ? scenarios['+10_tutors'] + 'h' : '-');
    }

    /**
     * Helper method to update DOM elements
     */
    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * Show forecasting error
     */
    showForecastingError() {
        const errorElements = [
            'nextWeekHours', 'nextWeekConfidence', 'nextWeekTrend', 'nextWeekCI', 'nextWeekMethods',
            'nextMonthHours', 'nextMonthConfidence', 'nextMonthTrend', 'nextMonthCI',
            'tutorDemandWeek', 'tutorDemandMonth',
            'busiestDay', 'busiestHour',
            'anomalyStatus', 'anomalyPercent', 'anomalyLastWeek', 'anomalyPrevAvg',
            'histLastWeek', 'histForecastWeek', 'histLastMonth', 'histForecastMonth',
            'forecastLastUpdated'
        ];

        errorElements.forEach(id => {
            this.updateElement(id, 'Error');
        });
    }

    /**
     * Show AI insights error
     */
    showAIInsightsError() {
        this.updateElement('aiConfidenceScore', 'Error');
        this.updateElement('forecastAccuracy', 'Error');
        
        const summaryElement = document.getElementById('improvedNLSummary');
        if (summaryElement) {
            const spanElement = summaryElement.querySelector('span');
            if (spanElement) {
                spanElement.textContent = 'Failed to load AI insights';
            }
        }
    }

    /**
     * Get recommendation card class
     */
    getRecommendationCardClass(priority) {
        switch (priority) {
            case 'high': return 'border-danger';
            case 'medium': return 'border-warning';
            case 'low': return 'border-info';
            default: return 'border-secondary';
        }
    }

    /**
     * Get recommendation icon
     */
    getRecommendationIcon(type) {
        switch (type) {
            case 'staffing': return 'fa-users';
            case 'schedule': return 'fa-clock';
            case 'quality': return 'fa-star';
            case 'growth': return 'fa-chart-line';
            case 'consistency': return 'fa-chart-bar';
            default: return 'fa-lightbulb';
        }
    }

    /**
     * Get priority badge class
     */
    getPriorityBadgeClass(priority) {
        switch (priority) {
            case 'high': return 'bg-danger';
            case 'medium': return 'bg-warning text-dark';
            case 'low': return 'bg-info';
            default: return 'bg-secondary';
        }
    }

    /**
     * Destroy all charts
     */
    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    /**
     * Refresh forecasting data
     */
    async refresh() {
        try {
            this.destroyCharts();
            await this.initialize();
        } catch (error) {
            console.error('Error refreshing forecasting data:', error);
        }
    }

    /**
     * Initialize charts for forecasting data
     */
    initializeCharts() {
        try {
            // Check if Chart.js is available
            if (typeof Chart === 'undefined') {
                console.log('Chart.js not available, skipping chart initialization');
                return;
            }

            // Initialize forecasting trend chart if element exists
            const forecastingChartCtx = document.getElementById('forecastingTrendChart');
            if (forecastingChartCtx && this.forecastingData) {
                this.createForecastingTrendChart(forecastingChartCtx);
            }

            // Initialize AI confidence chart if element exists
            const confidenceChartCtx = document.getElementById('aiConfidenceChart');
            if (confidenceChartCtx && this.aiInsights) {
                this.createAIConfidenceChart(confidenceChartCtx);
            }

            console.log('Charts initialized successfully');
        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }

    /**
     * Create forecasting trend chart
     */
    createForecastingTrendChart(ctx) {
        if (!this.forecastingData || !this.forecastingData.hourly_forecast) return;

        const hourlyData = this.forecastingData.hourly_forecast;
        const labels = Array.from({length: 24}, (_, i) => `${i.toString().padStart(2, '0')}:00`);
        const data = Array.from({length: 24}, (_, i) => hourlyData[i]?.predicted_hours || 0);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Predicted Hours',
                    data: data,
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '24-Hour Forecasting Trend'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Hours'
                        }
                    }
                }
            }
        });
    }

    /**
     * Create AI confidence chart
     */
    createAIConfidenceChart(ctx) {
        if (!this.aiInsights) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Confidence', 'Uncertainty'],
                datasets: [{
                    data: [this.aiInsights.confidence_score, 100 - this.aiInsights.confidence_score],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(200, 200, 200, 0.3)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'AI Confidence Score'
                    }
                }
            }
        });
    }
}

// Global forecasting manager instance
window.forecastingManager = new ForecastingManager();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize forecasting after a short delay to ensure other components are loaded
    setTimeout(() => {
        window.forecastingManager.initialize();
    }, 1000);
}); 