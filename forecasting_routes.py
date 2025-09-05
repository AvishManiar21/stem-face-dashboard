#!/usr/bin/env python3
"""
Forecasting and AI Insights API routes
Handles all forecasting and AI-related endpoints
"""

from flask import Blueprint, jsonify, request
from forecasting import TutorForecasting
from ai_insights import AIInsights
import logging
from datetime import datetime

# Create Blueprint
forecasting_bp = Blueprint('forecasting', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize forecasting and AI insights modules
forecasting_module = None
ai_insights_module = None

def initialize_modules():
    """Initialize forecasting and AI insights modules"""
    global forecasting_module, ai_insights_module
    try:
        forecasting_module = TutorForecasting()
        ai_insights_module = AIInsights()
        logger.info("Forecasting and AI insights modules initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing modules: {e}")

@forecasting_bp.route('/api/forecasting-data', methods=['GET'])
def get_forecasting_data():
    """Get comprehensive forecasting data"""
    try:
        if forecasting_module is None:
            initialize_modules()
        
        if forecasting_module is None:
            return jsonify({'error': 'Forecasting module not available'}), 500
        
        # Get all forecasting data
        forecast_summary = forecasting_module.get_forecast_summary()
        
        # Add additional data for frontend
        response_data = {
            'next_week_hours': forecast_summary.get('next_week', {}).get('predicted_hours', 0),
            'next_week_confidence': forecast_summary.get('next_week', {}).get('confidence', 0),
            'next_week_trend': forecast_summary.get('next_week', {}).get('trend', 'neutral'),
            'next_week_ci': forecast_summary.get('next_week', {}).get('confidence_interval', 'N/A'),
            'next_week_methods': forecast_summary.get('next_week', {}).get('methods', 'N/A'),
            
            'next_month_hours': forecast_summary.get('next_month', {}).get('predicted_hours', 0),
            'next_month_confidence': forecast_summary.get('next_month', {}).get('confidence', 0),
            'next_month_trend': forecast_summary.get('next_month', {}).get('trend', 'neutral'),
            'next_month_ci': forecast_summary.get('next_month', {}).get('confidence_interval', 'N/A'),
            
            'tutor_demand_week': forecast_summary.get('tutor_demand', {}).get('weekly_demand', 0),
            'tutor_demand_month': forecast_summary.get('tutor_demand', {}).get('monthly_demand', 0),
            
            'busiest_day': forecast_summary.get('busiest_patterns', {}).get('busiest_day', 'N/A'),
            'busiest_hour': forecast_summary.get('busiest_patterns', {}).get('busiest_hour', 'N/A'),
            
            'anomaly_status': forecast_summary.get('anomaly_detection', {}).get('status', 'N/A'),
            'anomaly_percent': forecast_summary.get('anomaly_detection', {}).get('anomaly_percent', 0),
            'anomaly_last_week': forecast_summary.get('anomaly_detection', {}).get('last_week_anomalies', 0),
            'anomaly_prev_avg': forecast_summary.get('anomaly_detection', {}).get('previous_avg', 0),
            
            'hist_last_week': forecast_summary.get('historical_comparison', {}).get('last_week', 0),
            'hist_forecast_week': forecast_summary.get('historical_comparison', {}).get('forecast_week', 0),
            'hist_last_month': forecast_summary.get('historical_comparison', {}).get('last_month', 0),
            'hist_forecast_month': forecast_summary.get('historical_comparison', {}).get('forecast_month', 0),
            
            'forecast_last_updated': forecast_summary.get('last_updated', 'N/A'),
            
            # Additional data for charts and tables
            'hourly_forecast': forecast_summary.get('hourly_forecast', {}),
            'daily_forecast': forecast_summary.get('daily_forecast', {}),
            'per_tutor_forecast': forecast_summary.get('per_tutor_forecast', {}),
            'scenario_simulation': forecast_summary.get('scenario_simulation', {}),
            
            # Placeholder data for charts (would be implemented in full version)
            'forecast_vs_actual_history': [
                {'week': 1, 'forecast': 45.2, 'actual': 42.1},
                {'week': 2, 'forecast': 48.7, 'actual': 47.3},
                {'week': 3, 'forecast': 51.3, 'actual': 49.8},
                {'week': 4, 'forecast': 53.9, 'actual': 52.4}
            ],
            'day_of_week_forecast': {
                'Monday': {'predicted_hours': 12.5},
                'Tuesday': {'predicted_hours': 14.2},
                'Wednesday': {'predicted_hours': 16.8},
                'Thursday': {'predicted_hours': 15.3},
                'Friday': {'predicted_hours': 13.7},
                'Saturday': {'predicted_hours': 8.9},
                'Sunday': {'predicted_hours': 6.4}
            },
            'forecast_explanation': 'Forecasts are based on historical patterns using linear regression models. Confidence scores reflect data quality and pattern consistency.'
        }
        
        logger.info("FORECASTING ENDPOINT CALLED")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in forecasting data endpoint: {e}")
        return jsonify({'error': 'Failed to load forecasting data'}), 500

@forecasting_bp.route('/api/ai-insights', methods=['GET'])
def get_ai_insights():
    """Get AI-generated insights and recommendations"""
    try:
        if ai_insights_module is None:
            initialize_modules()
        
        if ai_insights_module is None:
            return jsonify({'error': 'AI insights module not available'}), 500
        
        # Get AI insights
        insights_summary = ai_insights_module.get_insights_summary()
        
        # Format response for frontend
        response_data = {
            'nlp_summary': insights_summary.get('nlp_summary', 'No insights available'),
            'ai_recommendations': insights_summary.get('ai_recommendations', []),
            'confidence_score': insights_summary.get('confidence_score', 0),
            'forecast_accuracy': insights_summary.get('forecast_accuracy', 0),
            'growth_opportunities': insights_summary.get('growth_opportunities', []),
            'last_updated': insights_summary.get('last_updated', 'N/A')
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in AI insights endpoint: {e}")
        return jsonify({'error': 'Failed to load AI insights'}), 500

@forecasting_bp.route('/api/forecasting-summary', methods=['GET'])
def get_forecasting_summary():
    """Get a simplified forecasting summary for dashboard widgets"""
    try:
        if forecasting_module is None:
            initialize_modules()
        
        if forecasting_module is None:
            return jsonify({'error': 'Forecasting module not available'}), 500
        
        # Get key forecasting metrics
        weekly_forecast = forecasting_module.get_weekly_forecast()
        monthly_forecast = forecasting_module.get_monthly_forecast()
        demand_forecast = forecasting_module.get_tutor_demand_forecast()
        
        summary_data = {
            'next_week': {
                'hours': weekly_forecast.get('predicted_hours', 0),
                'confidence': weekly_forecast.get('confidence', 0),
                'trend': weekly_forecast.get('trend', 'neutral')
            },
            'next_month': {
                'hours': monthly_forecast.get('predicted_hours', 0),
                'confidence': monthly_forecast.get('confidence', 0),
                'trend': monthly_forecast.get('trend', 'neutral')
            },
            'tutor_demand': {
                'weekly': demand_forecast.get('weekly_demand', 0),
                'monthly': demand_forecast.get('monthly_demand', 0)
            },
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(summary_data)
        
    except Exception as e:
        logger.error(f"Error in forecasting summary endpoint: {e}")
        return jsonify({'error': 'Failed to load forecasting summary'}), 500

@forecasting_bp.route('/api/ai-confidence', methods=['GET'])
def get_ai_confidence():
    """Get AI confidence metrics"""
    try:
        if ai_insights_module is None:
            initialize_modules()
        
        if ai_insights_module is None:
            return jsonify({'error': 'AI insights module not available'}), 500
        
        confidence_data = {
            'confidence_score': ai_insights_module.calculate_confidence_score(),
            'forecast_accuracy': ai_insights_module.calculate_forecast_accuracy(),
            'data_quality': 'Good' if ai_insights_module.calculate_confidence_score() > 70 else 'Fair',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(confidence_data)
        
    except Exception as e:
        logger.error(f"Error in AI confidence endpoint: {e}")
        return jsonify({'error': 'Failed to load AI confidence data'}), 500

# Initialize modules when blueprint is created
initialize_modules() 