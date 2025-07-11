#!/usr/bin/env python3
"""
Forecasting module for tutor dashboard
Handles predictions, trends, and forecasting calculations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TutorForecasting:
    """
    Forecasting and trend analysis for tutor face recognition data.
    Provides predictions for hours, demand, and trends.
    """
    
    def __init__(self, face_log_file='logs/face_log_with_expected.csv', max_date=None):
        self.face_log_file = face_log_file
        self.max_date = max_date or pd.Timestamp.now().normalize()
        self.data = self.load_data()
        self.scaler = StandardScaler()
        
    def load_data(self):
        """Load and preprocess face log data for forecasting"""
        try:
            df = pd.read_csv(self.face_log_file)
            if df.empty:
                return pd.DataFrame()
            
            # Parse datetime columns
            df['check_in'] = pd.to_datetime(df['check_in'], format='mixed', errors='coerce')
            df['check_out'] = pd.to_datetime(df['check_out'], format='mixed', errors='coerce')
            
            # Filter to max_date if set
            if self.max_date is not None:
                df = df[df['check_in'].dt.date <= self.max_date.date()]
            
            # Add derived columns
            df['date'] = df['check_in'].dt.date
            df['date'] = df['date'].apply(lambda d: d if isinstance(d, date) else pd.to_datetime(d).date() if pd.notna(d) else None)
            df['day_of_week'] = df['check_in'].dt.day_name()
            df['hour'] = df['check_in'].dt.hour
            df['week'] = df['check_in'].dt.isocalendar().week
            df['month'] = df['check_in'].dt.month
            df['year'] = df['check_in'].dt.year
            
            return df.sort_values('check_in')
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading forecasting data: {e}")
            return pd.DataFrame()
    
    def get_weekly_forecast(self, weeks_ahead=1):
        """Predict hours for the next few weeks"""
        if self.data.empty:
            return {'predicted_hours': 0, 'confidence': 0, 'trend': 'neutral'}
        
        try:
            # Group by week and calculate total hours
            weekly_data = self.data.groupby(['year', 'week'])['shift_hours'].sum().reset_index()
            weekly_data['week_number'] = weekly_data.groupby('year').cumcount() + 1
            
            if len(weekly_data) < 3:
                return {'predicted_hours': 0, 'confidence': 0, 'trend': 'neutral'}
            
            # Prepare features for prediction
            X = weekly_data[['week_number']].values
            y = weekly_data['shift_hours'].values
            
            # Train model
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict next week
            next_week = weekly_data['week_number'].max() + weeks_ahead
            prediction = model.predict([[next_week]])[0]
            
            # Calculate confidence based on R-squared
            y_pred = model.predict(X)
            r_squared = 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2))
            confidence = max(0, min(100, r_squared * 100))
            
            # Determine trend
            if len(weekly_data) >= 2:
                recent_trend = weekly_data['shift_hours'].iloc[-1] - weekly_data['shift_hours'].iloc[-2]
                if recent_trend > 0:
                    trend = 'increasing'
                elif recent_trend < 0:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'neutral'
            
            return {
                'predicted_hours': round(prediction, 1),
                'confidence': round(confidence, 1),
                'trend': trend,
                'confidence_interval': f"±{round(prediction * 0.15, 1)}h",
                'methods': 'Linear Regression'
            }
            
        except Exception as e:
            logger.error(f"Error in weekly forecast: {e}")
            return {'predicted_hours': 0, 'confidence': 0, 'trend': 'neutral'}
    
    def get_monthly_forecast(self, months_ahead=1):
        """Predict hours for the next few months"""
        if self.data.empty:
            return {'predicted_hours': 0, 'confidence': 0, 'trend': 'neutral'}
        
        try:
            # Group by month and calculate total hours
            monthly_data = self.data.groupby(['year', 'month'])['shift_hours'].sum().reset_index()
            monthly_data['month_number'] = monthly_data.groupby('year').cumcount() + 1
            
            if len(monthly_data) < 3:
                return {'predicted_hours': 0, 'confidence': 0, 'trend': 'neutral'}
            
            # Prepare features for prediction
            X = monthly_data[['month_number']].values
            y = monthly_data['shift_hours'].values
            
            # Train model
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict next month
            next_month = monthly_data['month_number'].max() + months_ahead
            prediction = model.predict([[next_month]])[0]
            
            # Calculate confidence
            y_pred = model.predict(X)
            r_squared = 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2))
            confidence = max(0, min(100, r_squared * 100))
            
            # Determine trend
            if len(monthly_data) >= 2:
                recent_trend = monthly_data['shift_hours'].iloc[-1] - monthly_data['shift_hours'].iloc[-2]
                if recent_trend > 0:
                    trend = 'increasing'
                elif recent_trend < 0:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'neutral'
            
            return {
                'predicted_hours': round(prediction, 1),
                'confidence': round(confidence, 1),
                'trend': trend,
                'confidence_interval': f"±{round(prediction * 0.2, 1)}h"
            }
            
        except Exception as e:
            logger.error(f"Error in monthly forecast: {e}")
            return {'predicted_hours': 0, 'confidence': 0, 'trend': 'neutral'}
    
    def get_tutor_demand_forecast(self):
        """Predict tutor demand for upcoming periods"""
        if self.data.empty:
            return {'weekly_demand': 0, 'monthly_demand': 0}
        
        try:
            # Calculate unique tutors per week
            weekly_tutors = self.data.groupby(['year', 'week'])['tutor_id'].nunique()
            monthly_tutors = self.data.groupby(['year', 'month'])['tutor_id'].nunique()
            
            # Simple average prediction
            avg_weekly = weekly_tutors.mean()
            avg_monthly = monthly_tutors.mean()
            
            return {
                'weekly_demand': round(avg_weekly, 1),
                'monthly_demand': round(avg_monthly, 1)
            }
            
        except Exception as e:
            logger.error(f"Error in tutor demand forecast: {e}")
            return {'weekly_demand': 0, 'monthly_demand': 0}
    
    def get_busiest_patterns(self):
        """Identify busiest days and hours"""
        if self.data.empty:
            return {'busiest_day': 'N/A', 'busiest_hour': 'N/A'}
        
        try:
            # Busiest day
            day_counts = self.data.groupby('day_of_week').size()
            busiest_day = day_counts.idxmax() if not day_counts.empty else 'N/A'
            
            # Busiest hour
            hour_counts = self.data.groupby('hour').size()
            busiest_hour = f"{hour_counts.idxmax()}:00" if not hour_counts.empty else 'N/A'
            
            return {
                'busiest_day': busiest_day,
                'busiest_hour': busiest_hour
            }
            
        except Exception as e:
            logger.error(f"Error in busiest patterns: {e}")
            return {'busiest_day': 'N/A', 'busiest_hour': 'N/A'}
    
    def get_anomaly_detection(self):
        """Detect anomalies in the data"""
        if self.data.empty:
            return {'status': 'No data', 'anomaly_percent': 0}
        
        try:
            # Calculate daily hours
            daily_hours = self.data.groupby('date')['shift_hours'].sum()
            
            if len(daily_hours) < 7:
                return {'status': 'Insufficient data', 'anomaly_percent': 0}
            
            # Calculate statistics
            mean_hours = daily_hours.mean()
            std_hours = daily_hours.std()
            
            # Define anomalies as values outside 2 standard deviations
            anomalies = daily_hours[(daily_hours < mean_hours - 2*std_hours) | 
                                  (daily_hours > mean_hours + 2*std_hours)]
            
            anomaly_percent = (len(anomalies) / len(daily_hours)) * 100
            
            if anomaly_percent > 10:
                status = 'High anomalies detected'
            elif anomaly_percent > 5:
                status = 'Moderate anomalies'
            else:
                status = 'Normal patterns'
            
            return {
                'status': status,
                'anomaly_percent': round(anomaly_percent, 1),
                'last_week_anomalies': len(anomalies[-7:]) if len(anomalies) >= 7 else len(anomalies),
                'previous_avg': round(mean_hours, 1)
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {'status': 'Error', 'anomaly_percent': 0}
    
    def get_historical_vs_forecast(self):
        """Compare historical data with previous forecasts"""
        if self.data.empty:
            return {'last_week': 0, 'last_month': 0}
        
        try:
            # Calculate last week and last month totals
            last_week = (datetime.now() - timedelta(days=7)).date()
            last_month = (datetime.now() - timedelta(days=30)).date()
            
            last_week_data = self.data[self.data['date'] >= last_week]
            last_month_data = self.data[self.data['date'] >= last_month]
            
            last_week_hours = last_week_data['shift_hours'].sum()
            last_month_hours = last_month_data['shift_hours'].sum()
            
            return {
                'last_week': round(last_week_hours, 1),
                'last_month': round(last_month_hours, 1),
                'forecast_week': round(last_week_hours * 1.05, 1),  # Simple 5% growth assumption
                'forecast_month': round(last_month_hours * 1.05, 1)
            }
            
        except Exception as e:
            logger.error(f"Error in historical vs forecast: {e}")
            return {'last_week': 0, 'last_month': 0}
    
    def get_hourly_forecast(self):
        """Predict hourly patterns"""
        if self.data.empty:
            return {}
        
        try:
            # Calculate average hours per hour of day
            hourly_avg = self.data.groupby('hour')['shift_hours'].mean()
            
            # Predict next day's hourly pattern
            hourly_forecast = {}
            for hour in range(24):
                if hour in hourly_avg.index:
                    hourly_forecast[hour] = {
                        'predicted_hours': round(hourly_avg[hour], 1),
                        'predicted_sessions': round(hourly_avg[hour] / 2, 1)  # Assume 2 hours per session
                    }
                else:
                    hourly_forecast[hour] = {
                        'predicted_hours': 0,
                        'predicted_sessions': 0
                    }
            
            return hourly_forecast
            
        except Exception as e:
            logger.error(f"Error in hourly forecast: {e}")
            return {}
    
    def get_per_tutor_forecast(self):
        """Predict individual tutor performance"""
        if self.data.empty:
            return {}
        
        try:
            # Calculate average hours per tutor
            tutor_avg = self.data.groupby(['tutor_id', 'tutor_name'])['shift_hours'].agg(['mean', 'count']).reset_index()
            
            per_tutor_forecast = {}
            for _, row in tutor_avg.iterrows():
                tutor_id = str(row['tutor_id'])
                per_tutor_forecast[tutor_id] = {
                    'tutor_name': row['tutor_name'],
                    'predicted_hours': round(row['mean'] * 4, 1),  # Assume 4 weeks
                    'predicted_sessions': round(row['mean'] * 4 / 2, 1),  # Assume 2 hours per session
                    'confidence': min(100, max(0, row['count'] * 10))  # More data = higher confidence
                }
            
            return per_tutor_forecast
            
        except Exception as e:
            logger.error(f"Error in per-tutor forecast: {e}")
            return {}
    
    def get_scenario_simulation(self):
        """Simulate different scenarios (e.g., adding more tutors)"""
        if self.data.empty:
            return {}
        
        try:
            # Calculate current average daily hours
            daily_hours = self.data.groupby('date')['shift_hours'].sum()
            avg_daily_hours = daily_hours.mean()
            
            # Simulate adding more tutors
            scenarios = {}
            for additional_tutors in [2, 5, 10]:
                # Assume each tutor contributes 4 hours per day
                additional_hours = additional_tutors * 4 * 7  # 7 days per week
                scenarios[f'+{additional_tutors}_tutors'] = round(avg_daily_hours * 7 + additional_hours, 1)
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error in scenario simulation: {e}")
            return {}
    
    def get_forecast_summary(self):
        """Get a comprehensive forecast summary"""
        try:
            weekly = self.get_weekly_forecast()
            monthly = self.get_monthly_forecast()
            demand = self.get_tutor_demand_forecast()
            patterns = self.get_busiest_patterns()
            anomalies = self.get_anomaly_detection()
            historical = self.get_historical_vs_forecast()
            hourly = self.get_hourly_forecast()
            per_tutor = self.get_per_tutor_forecast()
            scenarios = self.get_scenario_simulation()
            
            return {
                'next_week': weekly,
                'next_month': monthly,
                'tutor_demand': demand,
                'busiest_patterns': patterns,
                'anomaly_detection': anomalies,
                'historical_comparison': historical,
                'hourly_forecast': hourly,
                'per_tutor_forecast': per_tutor,
                'scenario_simulation': scenarios,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error in forecast summary: {e}")
            return {} 