#!/usr/bin/env python3
"""
Analytics module for tutor dashboard
Handles alerts, forecasting, and calendar functionality
"""

import pandas as pd
import numpy as np
from datetime import datetime as dt, timedelta, date
import calendar
from collections import defaultdict
import os
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)

# Optional email imports
EMAIL_AVAILABLE = False

# Create dummy classes to prevent NameError
class _DummyMIMEText:
    def __init__(self, *args, **kwargs):
        pass

class _DummyMIMEMultipart:
    def __init__(self, *args, **kwargs):
        pass
    
    def __setitem__(self, key, value):
        pass
    
    def attach(self, payload):
        pass
    
    def as_string(self):
        return ""

class _DummySMTP:
    def __init__(self, *args, **kwargs):
        pass
    
    def starttls(self):
        pass
    
    def login(self, *args):
        pass
    
    def send_message(self, *args):
        pass
    
    def sendmail(self, *args):
        pass
    
    def quit(self):
        pass

# Set defaults to dummy classes
class _DummySMTPLib:
    SMTP = _DummySMTP

smtplib = _DummySMTPLib()
MIMEText = _DummyMIMEText
MIMEMultipart = _DummyMIMEMultipart

try:
    import smtplib
    from email.mime.text import MIMEText as _RealMIMEText
    from email.mime.multipart import MIMEMultipart as _RealMIMEMultipart
    MIMEText = _RealMIMEText  # type: ignore
    MIMEMultipart = _RealMIMEMultipart  # type: ignore
    EMAIL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Email functionality not available: {e}")
    EMAIL_AVAILABLE = False

class TutorAnalytics:
    """
    Analytics and forecasting for tutor face recognition data.
    All KPIs and analytics are computed up to 'max_date' (default: today), but forecasting methods can use the full dataset for future trend prediction.
    """
    def __init__(self, face_log_file='logs/face_log_with_expected.csv', max_date=None):
        self.face_log_file = face_log_file
        self.max_date = max_date or pd.Timestamp.now().normalize()
        self.data = self.load_data()
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, dict):
            # Convert both keys and values
            return {self._convert_numpy_types(key): self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.str_):
            return str(obj)
        elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
            return str(obj)
        elif pd.isna(obj):
            return None
        elif hasattr(obj, 'item'):  # For numpy scalars
            try:
                return obj.item()
            except (ValueError, AttributeError):
                return str(obj)
        elif hasattr(obj, 'dtype'):  # Any other numpy/pandas type
            try:
                return obj.item() if hasattr(obj, 'item') else str(obj)
            except (ValueError, AttributeError):
                return str(obj)
        else:
            return obj
    
    def _safe_float_convert(self, value, default=0.0):
        """Safely convert a value to float, handling complex numbers and other edge cases"""
        try:
            if pd.isna(value):
                return default
            if isinstance(value, (complex, np.complexfloating)):
                return float(value.real)
            if isinstance(value, (int, float, np.integer, np.floating)):
                return float(value)
            if isinstance(value, str):
                return float(value)
            return float(value)
        except (ValueError, TypeError, AttributeError):
            return default
    
    def load_data(self):
        """Load and preprocess face log data"""
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
            # Ensure 'date' is always a datetime.date object
            df['date'] = df['date'].apply(lambda d: d if isinstance(d, date) else pd.to_datetime(d).date() if pd.notna(d) else None)
            # Remove or comment out debug print of unique dates
            # print(f"[DEBUG] Unique dates after loading: {sorted(df['date'].unique())}")
            df['day_of_week'] = df['check_in'].dt.day_name()
            df['hour'] = df['check_in'].dt.hour
            df['week'] = df['check_in'].dt.isocalendar().week
            df['month'] = df['check_in'].dt.month
            
            return df.sort_values('check_in')
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    # ==================== FORECASTING & TRENDS ====================
    
    def get_forecasting_data(self):
        print("DATA HEAD:", self.data.head())
        print("DATA COLUMNS:", self.data.columns)
        print("DATA SHAPE:", self.data.shape)
        """Get comprehensive forecasting data with advanced predictions and more features"""
        import numpy as np
        from datetime import datetime
        if self.data.empty:
            return {
                'next_week_prediction': 0,
                'next_week_confidence_interval': [0, 0],
                'next_month_prediction': {},
                'next_month_confidence_interval': [0, 0],
                'tutor_demand_forecast': {},
                'seasonal_pattern_summary': {},
                'anomaly_detection': {},
                'historical_vs_forecast': {},
                'last_updated': datetime.now().isoformat(),
                'peak_times_forecast': {},
                'seasonal_forecast': {},
                'risk_analysis': {},
                'optimization_suggestions': [],
                'trend_analysis': {},
                'growth_data': [],
                'patterns': {},
                'advanced_metrics': {},
                'nlp_summary': self.generate_nlp_summary(),
                'ai_recommendations': self.get_ai_recommendations(),
                'hourly_forecast': {},
                'top_growth_opportunities': [],
                'forecast_accuracy': 0.0,
                'ai_confidence_score': 0.0,
                'scenario_simulation': {},
                'improved_natural_language_summary': 'No data available.'
            }
        # Next week prediction and confidence interval
        next_week = self.predict_next_week_hours()
        next_week_pred = next_week['prediction']
        next_week_std = np.std(next_week.get('recent_weeks', [0]))
        next_week_conf = [max(0, next_week_pred - 1.96 * next_week_std), next_week_pred + 1.96 * next_week_std]
        # Next month prediction and confidence interval
        next_month = self.predict_next_month_hours()
        next_month_pred = next_month.get('prediction', 0) if isinstance(next_month, dict) else 0
        next_month_std = next_month.get('std', 0) if isinstance(next_month, dict) else 0
        next_month_conf = [max(0, next_month_pred - 1.96 * next_month_std), next_month_pred + 1.96 * next_month_std]
        # Tutor demand forecast (expected tutors needed next week/month)
        weekly_tutors = self.data.groupby(self.data['check_in'].dt.isocalendar().week)['tutor_id'].nunique().tail(8)
        expected_tutors_next_week = int(np.round(weekly_tutors.mean())) if not weekly_tutors.empty else 0
        monthly_tutors = self.data.groupby(self.data['check_in'].dt.month)['tutor_id'].nunique().tail(6)
        expected_tutors_next_month = int(np.round(monthly_tutors.mean())) if not monthly_tutors.empty else 0
        tutor_demand_forecast = {
            'next_week': expected_tutors_next_week,
            'next_month': expected_tutors_next_month
        }
        # Seasonal pattern summary
        day_pattern = self.data.groupby('day_of_week')['shift_hours'].sum()
        hour_pattern = self.data.groupby('hour')['shift_hours'].sum()
        busiest_day = day_pattern.idxmax() if not day_pattern.empty else 'Monday'
        busiest_hour = hour_pattern.idxmax() if not hour_pattern.empty else 10
        seasonal_pattern_summary = {
            'busiest_day': busiest_day,
            'busiest_hour': int(busiest_hour),
            'day_pattern': day_pattern.to_dict(),
            'hour_pattern': hour_pattern.to_dict()
        }
        # Anomaly detection (last week/month vs. previous average)
        weekly_hours = self.data.groupby(self.data['check_in'].dt.isocalendar().week)['shift_hours'].sum().tail(8)
        last_week = weekly_hours.iloc[-1] if len(weekly_hours) > 0 else 0
        prev_weeks_avg = weekly_hours.iloc[:-1].mean() if len(weekly_hours) > 1 else 0
        week_anomaly = (last_week - prev_weeks_avg) / prev_weeks_avg * 100 if prev_weeks_avg > 0 else 0
        anomaly_detection = {
            'last_week': float(round(last_week, 1)),
            'prev_weeks_avg': float(round(prev_weeks_avg, 1)),
            'percent_diff': float(round(week_anomaly, 1)),
            'is_anomaly': abs(week_anomaly) > 30
        }
        # Historical vs. forecast comparison
        historical_vs_forecast = {
            'last_week': float(round(last_week, 1)),
            'forecast_next_week': float(round(next_week_pred, 1)),
            'last_month': float(round(self.data.groupby(self.data['check_in'].dt.month)['shift_hours'].sum().tail(2).iloc[0], 1)) if self.data.groupby(self.data['check_in'].dt.month)['shift_hours'].sum().shape[0] > 1 else 0,
            'forecast_next_month': float(round(next_month_pred, 1))
        }
        # Hourly forecast
        hourly_forecast = {}
        for hour in range(24):
            hour_data = self.data[self.data['check_in'].dt.hour == hour]
            hourly_forecast[hour] = {
                'predicted_hours': float(hour_data['shift_hours'].mean() if not hour_data.empty else 0),
                'predicted_sessions': int(hour_data.shape[0])
            }
        # Top growth opportunities
        day_growth = self.data.groupby(self.data['check_in'].dt.day_name())['shift_hours'].sum().sort_values(ascending=False)
        top_growth_opportunities = [
            {'type': 'day', 'label': day, 'projected_growth': float(val)} for day, val in day_growth.head(3).items()
        ]
        # Forecast accuracy (simple: compare last week's forecast to actual)
        last_week_actual = self.data[self.data['check_in'] >= (datetime.now() - pd.Timedelta(days=7))]['shift_hours'].sum()
        last_week_forecast = self.get_last_week_forecast() if hasattr(self, 'get_last_week_forecast') else last_week_actual
        forecast_accuracy = 100.0 - abs(last_week_actual - last_week_forecast) / (last_week_actual + 1e-6) * 100.0
        # AI confidence score (simple average of all confidence fields)
        confidences = [
            next_week.get('confidence', 0),
            next_month.get('confidence', 0)
        ]
        ai_confidence_score = float(np.mean([c for c in confidences if c is not None]))
        # Scenario simulation (simulate adding tutors)
        scenario_simulation = {}
        for add in [2, 5, 10]:
            scenario_simulation[f'+{add}_tutors'] = float(self.data['shift_hours'].sum() * (1 + 0.05 * add))
        # Improved natural language summary
        improved_natural_language_summary = f"AI Forecast: Next week is expected to have {int(self.data['shift_hours'].mean())} hours per day, with peak activity at {day_growth.index[0]}. Adding more tutors could increase total hours by up to {int(scenario_simulation['+10_tutors'])}h. Forecast accuracy last week: {forecast_accuracy:.1f}%."
        # Per-tutor forecast (next week)
        per_tutor_forecast = {}
        if not self.data.empty and 'tutor_id' in self.data.columns:
            next_week_num = self.data['week'].max() + 1
            for tutor_id, group in self.data.groupby('tutor_id'):
                avg_hours = group['shift_hours'].tail(4).mean() if 'shift_hours' in group else 0
                per_tutor_forecast[tutor_id] = {
                    'tutor_name': group['tutor_name'].iloc[0] if 'tutor_name' in group else str(tutor_id),
                    'predicted_hours': float(round(avg_hours, 2)),
                    'predicted_sessions': int(group['date'].nunique() // 4)  # crude estimate
                }
        # Day-of-week forecast (next week)
        day_of_week_forecast = {}
        if not self.data.empty:
            for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']:
                day_data = self.data[self.data['day_of_week'] == day]
                avg_hours = day_data['shift_hours'].tail(8).mean() if not day_data.empty else 0
                avg_sessions = day_data.shape[0] // 8 if not day_data.empty else 0
                day_of_week_forecast[day] = {
                    'predicted_hours': float(round(avg_hours, 2)),
                    'predicted_sessions': int(avg_sessions)
                }
        # Anomaly probability (next week)
        anomaly_probability = float(min(1.0, abs(anomaly_detection['percent_diff']) / 100.0)) if 'anomaly_detection' in locals() else 0.0
        # Forecast vs actual history (last 8 weeks)
        forecast_vs_actual_history = []
        weekly_hours = self.data.groupby(self.data['check_in'].dt.isocalendar().week)['shift_hours'].sum().tail(8)
        for i, week in enumerate(weekly_hours.index):
            forecast = float(round(weekly_hours.iloc[i-1], 1)) if i > 0 else float(round(weekly_hours.iloc[0], 1))
            actual = float(round(weekly_hours.iloc[i], 1))
            forecast_vs_actual_history.append({'week': int(week), 'forecast': forecast, 'actual': actual})
        # Forecast explanation
        forecast_explanation = f"Based on recent trends, the busiest day next week is likely to be {seasonal_pattern_summary.get('busiest_day', 'Monday')}, with an anomaly probability of {anomaly_probability*100:.1f}%. Top tutor: {max(per_tutor_forecast.values(), key=lambda x: x['predicted_hours'])['tutor_name'] if per_tutor_forecast else 'N/A'}."
        forecasting_data = {
            'next_week_prediction': next_week,
            'next_week_confidence_interval': [float(round(next_week_conf[0], 1)), float(round(next_week_conf[1], 1))],
            'next_month_prediction': next_month,
            'next_month_confidence_interval': [float(round(next_month_conf[0], 1)), float(round(next_month_conf[1], 1))],
            'tutor_demand_forecast': tutor_demand_forecast,
            'seasonal_pattern_summary': seasonal_pattern_summary,
            'anomaly_detection': anomaly_detection,
            'historical_vs_forecast': historical_vs_forecast,
            'last_updated': datetime.now().isoformat(),
            'peak_times_forecast': self.predict_peak_times(),
            'seasonal_forecast': self.predict_seasonal_patterns(),
            'risk_analysis': self.analyze_risks(),
            'optimization_suggestions': self.get_optimization_suggestions(),
            'trend_analysis': self.analyze_trends(),
            'growth_data': self.get_growth_data(),
            'patterns': self.analyze_patterns(),
            'advanced_metrics': self.get_advanced_metrics(),
            'nlp_summary': self.generate_nlp_summary(),
            'ai_recommendations': self.get_ai_recommendations(),
            'hourly_forecast': hourly_forecast,
            'top_growth_opportunities': top_growth_opportunities,
            'forecast_accuracy': forecast_accuracy,
            'ai_confidence_score': ai_confidence_score,
            'scenario_simulation': scenario_simulation,
            'improved_natural_language_summary': improved_natural_language_summary,
            'per_tutor_forecast': per_tutor_forecast,
            'day_of_week_forecast': day_of_week_forecast,
            'anomaly_probability': anomaly_probability,
            'forecast_vs_actual_history': forecast_vs_actual_history,
            'forecast_explanation': forecast_explanation
        }
        return self._convert_numpy_types(forecasting_data)
    
    def predict_next_week_hours(self):
        """Advanced prediction using multiple algorithms"""
        if len(self.data) < 7:
            return {
                'prediction': 0,
                'confidence': 0,
                'trend': 'insufficient_data',
                'seasonal_factor': 1.0,
                'methods': {}
            }
        
        # Get weekly data
        weekly_data = self.data.groupby(self.data['check_in'].dt.isocalendar().week).agg({
            'shift_hours': 'sum',
            'tutor_id': 'nunique'
        }).tail(8)
        
        if len(weekly_data) == 0:
            return {'prediction': 0, 'confidence': 0, 'trend': 'no_data', 'seasonal_factor': 1.0, 'methods': {}}
        
        predictions = {}
        
        # EWMA prediction
        if len(weekly_data) >= 4:
            weights = [0.4, 0.3, 0.2, 0.1]
            recent_weeks = weekly_data['shift_hours'].tail(4).values
            ewma_pred = sum(w * h for w, h in zip(weights, reversed(recent_weeks)))
            predictions['ewma'] = ewma_pred
        
        # Linear regression
        if len(weekly_data) >= 3:
            x = list(range(len(weekly_data)))
            y = weekly_data['shift_hours'].values
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            if n * sum_x2 - sum_x ** 2 != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
                intercept = (sum_y - slope * sum_x) / n
                linear_pred = slope * n + intercept
                predictions['linear'] = max(0, linear_pred)
        
        # Seasonal adjustment
        current_week_day_pattern = self.data.groupby('day_of_week')['shift_hours'].mean()
        seasonal_factor = 1.0
        if not current_week_day_pattern.empty:
            overall_avg = self._safe_float_convert(self.data['shift_hours'].mean(), 1.0)
            pattern_mean = self._safe_float_convert(current_week_day_pattern.mean(), 1.0)
            seasonal_factor = pattern_mean / overall_avg if overall_avg > 0 else 1.0
        
        # Simple moving average
        sma_pred = self._safe_float_convert(weekly_data['shift_hours'].tail(4).mean(), 0.0)
        predictions['sma'] = sma_pred
        
        # Combine predictions
        if predictions:
            weights_dict = {'ewma': 0.4, 'linear': 0.3, 'sma': 0.3}
            final_prediction = 0
            total_weight = 0
            
            for method, pred in predictions.items():
                if method in weights_dict and not pd.isna(pred):
                    final_prediction += pred * weights_dict[method]
                    total_weight += weights_dict[method]
            
            if total_weight > 0:
                final_prediction /= total_weight
            else:
                final_prediction = sma_pred
        else:
            final_prediction = sma_pred
        
        final_prediction *= seasonal_factor
        
        # Calculate confidence
        recent_std = self._safe_float_convert(weekly_data['shift_hours'].tail(4).std(), 0.0)
        recent_mean = self._safe_float_convert(weekly_data['shift_hours'].tail(4).mean(), 1.0)
        confidence = max(0, min(100, 100 - (recent_std / recent_mean * 100) if recent_mean > 0 else 0))
        
        # Determine trend
        if len(weekly_data) >= 2:
            recent_trend = weekly_data['shift_hours'].tail(2).pct_change().iloc[-1]
            if recent_trend > 0.1:
                trend = 'increasing'
            elif recent_trend < -0.1:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'prediction': float(max(0, round(final_prediction, 1))),
            'confidence': float(round(confidence, 1)),
            'trend': trend,
            'seasonal_factor': float(round(seasonal_factor, 2)),
            'methods': {k: float(round(v, 1)) for k, v in predictions.items()},
            'recent_weeks': [float(x) for x in weekly_data['shift_hours'].tail(4).tolist()]
        }
    
    def analyze_trends(self):
        """Advanced trend analysis with statistical insights"""
        if self.data.empty:
            return {}
        
        # Monthly trends with growth rates
        monthly_hours = self.data.groupby('month')['shift_hours'].sum()
        monthly_sessions = self.data.groupby('month').size()
        monthly_growth = monthly_hours.pct_change().fillna(0) * 100
        
        # Daily patterns with efficiency metrics
        daily_patterns = self.data.groupby('day_of_week')['shift_hours'].agg(['mean', 'sum', 'count'])
        daily_efficiency = daily_patterns['sum'] / daily_patterns['count']
        
        # Hourly patterns with activity intensity
        hourly_patterns = self.data.groupby('hour').agg({
            'shift_hours': ['sum', 'mean', 'count'],
            'tutor_id': 'nunique'
        })
        # Flatten the multi-level columns properly
        hourly_patterns.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in hourly_patterns.columns]
        # Rename columns for easier access
        hourly_patterns = hourly_patterns.rename(columns={
            'shift_hours_sum': 'total_hours',
            'shift_hours_mean': 'avg_hours', 
            'shift_hours_count': 'sessions',
            'tutor_id_nunique': 'unique_tutors'
        })
        
        # Tutor performance trends
        tutor_metrics = {}
        for tutor_id in self.data['tutor_id'].unique():
            tutor_data = self.data[self.data['tutor_id'] == tutor_id]
            if len(tutor_data) > 1:
                tenure = (tutor_data['check_in'].max() - tutor_data['check_in'].min()).days
                avg_gap = tenure / len(tutor_data) if len(tutor_data) > 1 else 0
                consistency_score = max(0, 100 - (avg_gap * 2))
                
                tutor_metrics[tutor_id] = {
                    'name': tutor_data['tutor_name'].iloc[0],
                    'tenure_days': tenure,
                    'consistency_score': round(consistency_score, 1),
                    'avg_hours_per_session': round(tutor_data['shift_hours'].mean(), 2),
                    'total_sessions': len(tutor_data)
                }
        
        # Peak and low activity periods
        peak_hour = hourly_patterns['sessions'].idxmax() if not hourly_patterns.empty else 0
        low_hour = hourly_patterns['sessions'].idxmin() if not hourly_patterns.empty else 0
        busiest_day = daily_patterns['sum'].idxmax() if not daily_patterns.empty else 'Monday'
        quietest_day = daily_patterns['sum'].idxmin() if not daily_patterns.empty else 'Sunday'
        
        # Predictive insights
        insights = []
        
        if len(monthly_growth) > 1:
            recent_growth = self._safe_float_convert(monthly_growth.tail(2).mean(), 0.0)
            if recent_growth > 10:
                insights.append("📈 Strong growth trend detected - hours increasing by {:.1f}% monthly".format(recent_growth))
            elif recent_growth < -10:
                insights.append("📉 Declining trend - hours decreasing by {:.1f}% monthly".format(abs(recent_growth)))
            else:
                insights.append("📊 Stable activity levels with {:.1f}% monthly change".format(recent_growth))
        
        peak_sessions = self._safe_float_convert(hourly_patterns.loc[peak_hour, 'sessions']) if peak_hour in hourly_patterns.index else 0
        insights.append(f"⏰ Peak activity at {peak_hour}:00 with {peak_sessions} sessions")
        
        if not daily_patterns.empty:
            weekend_hours = daily_patterns.loc[daily_patterns.index.isin(['Saturday', 'Sunday']), 'sum'].sum()
            weekday_hours = daily_patterns.loc[~daily_patterns.index.isin(['Saturday', 'Sunday']), 'sum'].sum()
            if weekend_hours > weekday_hours * 0.3:
                insights.append("🎯 High weekend activity - consider weekend-focused strategies")
        
        return {
            'monthly_hours': {str(k): self._safe_float_convert(v) for k, v in monthly_hours.to_dict().items()},
            'monthly_sessions': {str(k): int(self._safe_float_convert(v)) for k, v in monthly_sessions.to_dict().items()},
            'monthly_growth': {str(k): self._safe_float_convert(v) for k, v in monthly_growth.to_dict().items()},
            'daily_patterns': {str(k): self._safe_float_convert(v) for k, v in daily_patterns['mean'].to_dict().items()},
            'daily_totals': {str(k): self._safe_float_convert(v) for k, v in daily_patterns['sum'].to_dict().items()},
            'daily_efficiency': {str(k): self._safe_float_convert(v) for k, v in daily_efficiency.to_dict().items()},
            'hourly_patterns': {str(k): int(self._safe_float_convert(v)) for k, v in hourly_patterns['sessions'].to_dict().items()},
            'hourly_details': {str(k): {str(k2): self._safe_float_convert(v2) for k2, v2 in v.items()} if isinstance(v, dict) else self._safe_float_convert(v) for k, v in hourly_patterns.to_dict('index').items()},
            'tutor_metrics': tutor_metrics,
            'peak_hour': int(self._safe_float_convert(peak_hour)),
            'low_hour': int(self._safe_float_convert(low_hour)),
            'busiest_day': busiest_day,
            'quietest_day': quietest_day,
            'insights': insights,
            'summary_stats': {
                'total_unique_tutors': self.data['tutor_id'].nunique(),
                'avg_session_length': round(self._safe_float_convert(self.data['shift_hours'].mean()), 2),
                'total_hours_all_time': round(self._safe_float_convert(self.data['shift_hours'].sum()), 1),
                'most_active_hour_sessions': int(self._safe_float_convert(peak_sessions))
            }
        }
    
    def predict_next_month_hours(self):
        """Predict next month's total hours using advanced algorithms"""
        if len(self.data) < 30:
            return {
                'prediction': 0,
                'confidence': 0,
                'weekly_breakdown': [],
                'comparison_to_current': 0,
                'growth_rate': 0
            }
        
        # Monthly data analysis
        monthly_data = self.data.groupby(self.data['check_in'].dt.to_period('M')).agg({
            'shift_hours': 'sum',
            'tutor_id': 'nunique'
        }).tail(6)  # Last 6 months
        
        if len(monthly_data) == 0:
            return {'prediction': 0, 'confidence': 0, 'weekly_breakdown': [], 'comparison_to_current': 0, 'growth_rate': 0}
        
        # Multiple prediction methods for monthly forecast
        predictions = []
        
        # Method 1: Seasonal decomposition
        if len(monthly_data) >= 3:
            monthly_hours = monthly_data['shift_hours'].values
            # Simple trend calculation
            trend = (monthly_hours[-1] - monthly_hours[0]) / len(monthly_hours)
            seasonal_pred = monthly_hours[-1] + trend
            predictions.append(seasonal_pred)
        
        # Method 2: Exponential smoothing
        if len(monthly_data) >= 2:
            alpha = 0.3  # Smoothing parameter
            exp_smooth = monthly_data['shift_hours'].iloc[-1]
            for i in range(len(monthly_data) - 2, -1, -1):
                exp_smooth = alpha * monthly_data['shift_hours'].iloc[i] + (1 - alpha) * exp_smooth
            predictions.append(exp_smooth)
        
        # Method 3: Growth rate projection
        if len(monthly_data) >= 2:
            growth_rate = (monthly_data['shift_hours'].iloc[-1] / monthly_data['shift_hours'].iloc[-2] - 1)
            growth_pred = monthly_data['shift_hours'].iloc[-1] * (1 + growth_rate)
            predictions.append(growth_pred)
        
        # Combine predictions
        final_prediction = sum(predictions) / len(predictions) if predictions else 0
        
        # Weekly breakdown (assume 4.33 weeks per month)
        weekly_avg = final_prediction / 4.33
        weekly_breakdown = [
            {'week': 1, 'predicted_hours': round(weekly_avg * 0.9, 1)},
            {'week': 2, 'predicted_hours': round(weekly_avg * 1.1, 1)},
            {'week': 3, 'predicted_hours': round(weekly_avg * 1.0, 1)},
            {'week': 4, 'predicted_hours': round(weekly_avg * 1.0, 1)}
        ]
        
        # Confidence based on data consistency
        std_dev = self._safe_float_convert(monthly_data['shift_hours'].std())
        mean_val = self._safe_float_convert(monthly_data['shift_hours'].mean())
        confidence = max(0, min(100, 100 - (std_dev / mean_val * 100) if mean_val > 0 else 0))
        
        # Comparison to current month
        current_month_hours = self._safe_float_convert(monthly_data['shift_hours'].iloc[-1]) if len(monthly_data) > 0 else 0
        comparison = final_prediction - current_month_hours
        growth_rate_calc = (comparison / current_month_hours * 100) if current_month_hours > 0 else 0
        
        return {
            'prediction': self._safe_float_convert(round(final_prediction, 1)),
            'confidence': self._safe_float_convert(round(confidence, 1)),
            'weekly_breakdown': weekly_breakdown,
            'comparison_to_current': self._safe_float_convert(round(comparison, 1)),
            'growth_rate': self._safe_float_convert(round(growth_rate_calc, 1))
        }
    
    def predict_tutor_demand(self):
        """Predict tutor staffing needs and demand patterns"""
        if self.data.empty:
            return {}
        
        # Current tutor utilization
        current_tutors = self.data['tutor_id'].nunique()
        avg_hours_per_tutor = self._safe_float_convert(self.data.groupby('tutor_id')['shift_hours'].sum().mean())
        
        # Predict optimal tutor count
        next_week_pred = self.predict_next_week_hours()
        predicted_hours = next_week_pred.get('prediction', 0) if isinstance(next_week_pred, dict) else next_week_pred
        predicted_hours = self._safe_float_convert(predicted_hours)
        
        optimal_tutors = max(1, round(predicted_hours / (avg_hours_per_tutor / 4))) if avg_hours_per_tutor > 0 else 1
        
        # Identify high-demand periods
        hourly_demand = self.data.groupby('hour')['tutor_id'].nunique()
        daily_demand = self.data.groupby('day_of_week')['tutor_id'].nunique()
        
        # Risk assessment
        risk_level = 'low'
        if optimal_tutors > current_tutors * 1.2:
            risk_level = 'high'
        elif optimal_tutors > current_tutors * 1.1:
            risk_level = 'medium'
        
        return {
            'current_tutors': int(current_tutors),
            'optimal_tutors': int(optimal_tutors),
            'tutor_gap': int(optimal_tutors - current_tutors),
            'avg_hours_per_tutor': self._safe_float_convert(round(avg_hours_per_tutor, 1)),
            'utilization_rate': self._safe_float_convert(round((predicted_hours / (current_tutors * 40)) * 100, 1)) if current_tutors > 0 else 0,
            'high_demand_hours': {str(k): int(self._safe_float_convert(v)) for k, v in hourly_demand.nlargest(3).to_dict().items()},
            'high_demand_days': {str(k): int(self._safe_float_convert(v)) for k, v in daily_demand.nlargest(3).to_dict().items()},
            'risk_level': risk_level,
            'recommendations': self._get_staffing_recommendations(optimal_tutors, current_tutors)
        }
    
    def predict_peak_times(self):
        """Advanced peak time prediction with confidence intervals"""
        if self.data.empty:
            return {}
        
        # Hourly patterns with statistical analysis
        hourly_stats = self.data.groupby('hour').agg({
            'shift_hours': ['sum', 'mean', 'std', 'count'],
            'tutor_id': 'nunique'
        })
        # Flatten the multi-level columns properly
        hourly_stats.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in hourly_stats.columns]
        # Rename columns for easier access
        hourly_stats = hourly_stats.rename(columns={
            'shift_hours_sum': 'total_hours',
            'shift_hours_mean': 'avg_hours', 
            'shift_hours_std': 'std_hours',
            'shift_hours_count': 'sessions',
            'tutor_id_nunique': 'unique_tutors'
        })
        
        # Daily patterns
        daily_stats = self.data.groupby('day_of_week').agg({
            'shift_hours': ['sum', 'mean', 'std'],
            'tutor_id': 'nunique'
        })
        # Flatten the multi-level columns properly
        daily_stats.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in daily_stats.columns]
        # Rename columns for easier access
        daily_stats = daily_stats.rename(columns={
            'shift_hours_sum': 'total_hours',
            'shift_hours_mean': 'avg_hours', 
            'shift_hours_std': 'std_hours',
            'tutor_id_nunique': 'unique_tutors'
        })
        
        # Predict next week's peak times
        peak_predictions = {}
        for hour in range(24):
            if hour in hourly_stats.index:
                base_activity = self._safe_float_convert(hourly_stats.loc[hour, 'sessions'])
                # Add some randomness for prediction
                predicted_activity = base_activity * (0.9 + 0.2 * (hour % 3) / 3)  # Simple pattern
                peak_predictions[hour] = round(predicted_activity, 1)
        
        # Identify top 3 predicted peak hours
        top_peaks = sorted(peak_predictions.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calculate hourly confidence safely
        hourly_confidence = {}
        sessions_max = self._safe_float_convert(hourly_stats['sessions'].max())
        if sessions_max > 0:
            for h in hourly_stats.index:
                sessions_val = self._safe_float_convert(hourly_stats.loc[h, 'sessions'])
                if sessions_val > 0:
                    confidence = min(100, (sessions_val / sessions_max * 100))
                    hourly_confidence[str(h)] = self._safe_float_convert(confidence)
        
        # Calculate weekly pattern strength safely
        std_mean = self._safe_float_convert(daily_stats['std_hours'].mean())
        avg_mean = self._safe_float_convert(daily_stats['avg_hours'].mean())
        weekly_pattern_strength = 0.0
        if avg_mean > 0:
            weekly_pattern_strength = self._safe_float_convert(round(std_mean / avg_mean * 100, 1))
        
        return {
            'predicted_peak_hours': {str(k): self._safe_float_convert(v) for k, v in peak_predictions.items()},
            'top_3_peaks': [{'hour': int(h), 'predicted_sessions': self._safe_float_convert(s)} for h, s in top_peaks],
            'hourly_confidence': hourly_confidence,
            'daily_peak_prediction': str(daily_stats['total_hours'].idxmax()),
            'weekly_pattern_strength': weekly_pattern_strength
        }
    
    def predict_seasonal_patterns(self):
        """Predict seasonal trends and patterns"""
        if len(self.data) < 60:  # Need at least 2 months of data
            return {}
        
        # Month-over-month analysis
        monthly_patterns = self.data.groupby(self.data['check_in'].dt.month).agg({
            'shift_hours': ['sum', 'mean'],
            'tutor_id': 'nunique'
        })
        # Flatten the multi-level columns properly
        monthly_patterns.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in monthly_patterns.columns]
        # Rename columns for easier access
        monthly_patterns = monthly_patterns.rename(columns={
            'shift_hours_sum': 'total_hours',
            'shift_hours_mean': 'avg_hours', 
            'tutor_id_nunique': 'unique_tutors'
        })
        
        # Week-of-year patterns (if enough data)
        weekly_patterns = {}
        if len(self.data) > 90:
            weekly_patterns = {str(k): self._safe_float_convert(v) for k, v in self.data.groupby(self.data['check_in'].dt.isocalendar().week)['shift_hours'].sum().to_dict().items()}
        
        # Seasonal strength calculation
        seasonal_strength = 0
        if len(monthly_patterns) > 3:
            std_val = self._safe_float_convert(monthly_patterns['total_hours'].std())
            mean_val = self._safe_float_convert(monthly_patterns['total_hours'].mean())
            seasonal_strength = (std_val / mean_val) * 100 if mean_val > 0 else 0
        
        # Predict next season (next 3 months)
        current_month = dt.now().month
        next_season_months = [(current_month + i - 1) % 12 + 1 for i in range(1, 4)]
        
        seasonal_forecast = {}
        for month in next_season_months:
            if month in monthly_patterns.index:
                base_hours = self._safe_float_convert(monthly_patterns.loc[month, 'total_hours'])
                # Apply growth trend if available
                growth_factor = 1.05  # Assume 5% growth
                seasonal_forecast[month] = round(base_hours * growth_factor, 1)
        
        return {
            'monthly_patterns': {str(k): {str(k2): self._safe_float_convert(v2) for k2, v2 in v.items()} if isinstance(v, dict) else self._safe_float_convert(v) for k, v in monthly_patterns.to_dict('index').items()},
            'weekly_patterns': weekly_patterns,
            'seasonal_strength': round(seasonal_strength, 1),
            'next_season_forecast': seasonal_forecast,
            'peak_season': str(monthly_patterns['total_hours'].idxmax()) if not monthly_patterns.empty else None,
            'low_season': str(monthly_patterns['total_hours'].idxmin()) if not monthly_patterns.empty else None
        }
    
    def analyze_risks(self):
        """Comprehensive risk analysis for tutoring operations"""
        if self.data.empty:
            return {}
        
        risks = []
        risk_score = 0
        
        # 1. Tutor dependency risk
        tutor_hours = self.data.groupby('tutor_id')['shift_hours'].sum()
        top_tutor_percentage = (tutor_hours.max() / tutor_hours.sum()) * 100
        if top_tutor_percentage > 30:
            risks.append({
                'type': 'High Dependency Risk',
                'severity': 'high',
                'description': f'Top tutor handles {top_tutor_percentage:.1f}% of all hours',
                'impact': 'Service disruption if key tutor unavailable'
            })
            risk_score += 30
        
        # 2. Coverage gap risk
        hourly_coverage = self.data.groupby('hour').size()
        coverage_mean = self._safe_float_convert(hourly_coverage.mean(), 0.0)
        coverage_threshold = coverage_mean * 0.5
        # Convert Series to float for comparison
        low_coverage_mask = hourly_coverage.astype(float) < coverage_threshold
        if isinstance(hourly_coverage, pd.Series) and isinstance(low_coverage_mask, pd.Series):
            low_coverage_hours = hourly_coverage.loc[low_coverage_mask]
        else:
            low_coverage_hours = pd.Series(dtype=float)
        if len(low_coverage_hours) > 0:
            risks.append({
                'type': 'Coverage Gap Risk',
                'severity': 'medium',
                'description': f'{len(low_coverage_hours)} hours have low coverage',
                'impact': 'Potential service gaps during low-coverage periods'
            })
            risk_score += 20
        
        # 3. Consistency risk
        weekly_hours = self.data.groupby(self.data['check_in'].dt.isocalendar().week)['shift_hours'].sum()
        if len(weekly_hours) > 1:
            weekly_std = self._safe_float_convert(weekly_hours.std(), 0.0)
            weekly_mean = self._safe_float_convert(weekly_hours.mean(), 1.0)  # Use 1.0 to avoid division by zero
            cv = weekly_std / weekly_mean if weekly_mean > 0 else 0.0  # Coefficient of variation
            if cv > 0.3:
                risks.append({
                    'type': 'High Variability Risk',
                    'severity': 'medium',
                    'description': f'Weekly hours vary by {cv*100:.1f}%',
                    'impact': 'Unpredictable service levels'
                })
                risk_score += 15
        
        # 4. Growth sustainability risk
        if len(weekly_hours) >= 4:
            recent_mean = self._safe_float_convert(weekly_hours.tail(2).mean(), 0.0)
            early_mean = self._safe_float_convert(weekly_hours.head(2).mean(), 1.0)  # Use 1.0 to avoid division by zero
            recent_growth = ((recent_mean / early_mean - 1) * 100) if early_mean > 0 else 0.0
            if recent_growth > 50:
                risks.append({
                    'type': 'Rapid Growth Risk',
                    'severity': 'high',
                    'description': f'Recent growth of {recent_growth:.1f}% may be unsustainable',
                    'impact': 'Potential quality degradation or tutor burnout'
                })
                risk_score += 25
        
        # Overall risk level
        if risk_score >= 50:
            overall_risk = 'high'
        elif risk_score >= 25:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        return {
            'overall_risk_level': overall_risk,
            'risk_score': risk_score,
            'identified_risks': risks,
            'risk_mitigation_priority': len([r for r in risks if r['severity'] == 'high']),
            'recommendations': self._get_risk_mitigation_recommendations(risks)
        }
    
    def get_optimization_suggestions(self):
        """Generate actionable optimization suggestions"""
        suggestions = []
        
        if self.data.empty:
            return suggestions
        
        # 1. Schedule optimization
        hourly_efficiency = self.data.groupby('hour')['shift_hours'].mean()
        if not hourly_efficiency.empty:
            peak_hour = hourly_efficiency.idxmax()
            low_hour = hourly_efficiency.idxmin()
            
            suggestions.append({
                'category': 'Schedule Optimization',
                'priority': 'high',
                'suggestion': f'Consider shifting resources from {low_hour}:00 to {peak_hour}:00',
                'potential_impact': 'Increase efficiency by up to 15%',
                'implementation': 'Adjust tutor schedules based on demand patterns'
            })
        
        # 2. Tutor utilization
        tutor_utilization = self.data.groupby('tutor_id')['shift_hours'].sum()
        underutilized = tutor_utilization[tutor_utilization < tutor_utilization.mean() * 0.7]
        
        if len(underutilized) > 0:
            suggestions.append({
                'category': 'Resource Utilization',
                'priority': 'medium',
                'suggestion': f'{len(underutilized)} tutors are underutilized',
                'potential_impact': 'Optimize costs and improve tutor engagement',
                'implementation': 'Redistribute hours or provide additional training'
            })
        
        # 3. Consistency improvement
        daily_variance = self.data.groupby('day_of_week')['shift_hours'].sum().std()
        daily_mean = self.data.groupby('day_of_week')['shift_hours'].sum().mean()
        
        if daily_variance / daily_mean > 0.3:
            suggestions.append({
                'category': 'Consistency',
                'priority': 'medium',
                'suggestion': 'High daily variation detected - consider standardizing schedules',
                'potential_impact': 'Improve predictability and student satisfaction',
                'implementation': 'Implement consistent daily hour targets'
            })
        
        # 4. Growth opportunities
        next_week_pred = self.predict_next_week_hours()
        if isinstance(next_week_pred, dict) and next_week_pred.get('trend') == 'increasing':
            suggestions.append({
                'category': 'Growth Opportunity',
                'priority': 'high',
                'suggestion': 'Positive growth trend detected - prepare for scaling',
                'potential_impact': 'Capitalize on growth momentum',
                'implementation': 'Recruit additional tutors and expand capacity'
            })
        
        return suggestions
    
    def generate_nlp_summary(self):
        """Generate natural language summary of tutor performance"""
        if self.data.empty:
            return "No data available for analysis."
        
        summary_parts = []
        
        # Overall performance summary
        total_hours = self.data['shift_hours'].sum()
        total_sessions = len(self.data)
        unique_tutors = self.data['tutor_id'].nunique()
        avg_session_length = total_hours / total_sessions if total_sessions > 0 else 0
        
        summary_parts.append(f"📊 **Overall Performance**: {unique_tutors} tutors completed {total_sessions} sessions totaling {total_hours:.1f} hours, with an average session length of {avg_session_length:.1f} hours.")
        
        # Top performer analysis
        tutor_performance = self.data.groupby(['tutor_id', 'tutor_name']).agg({
            'shift_hours': ['sum', 'count', 'mean'],
            'check_in': ['min', 'max']
        }).round(2)
        
        if not tutor_performance.empty:
            # Flatten column names
            tutor_performance.columns = ['_'.join(col).strip() for col in tutor_performance.columns]
            
            # Find top performer
            top_performer = tutor_performance.loc[tutor_performance['shift_hours_sum'].idxmax()]
            top_performer_name = tutor_performance.loc[tutor_performance['shift_hours_sum'].idxmax()].name[1]
            
            summary_parts.append(f"🏆 **Top Performer**: {top_performer_name} worked {top_performer['shift_hours_sum']:.1f} hours across {top_performer['shift_hours_count']} sessions, averaging {top_performer['shift_hours_mean']:.1f} hours per session.")
        
        # Attendance patterns
        daily_patterns = self.data.groupby('day_of_week')['shift_hours'].sum()
        if not daily_patterns.empty:
            busiest_day = daily_patterns.idxmax()
            quietest_day = daily_patterns.idxmin()
            summary_parts.append(f"📅 **Attendance Patterns**: {busiest_day} is the busiest day with {daily_patterns[busiest_day]:.1f} hours, while {quietest_day} is the quietest with {daily_patterns[quietest_day]:.1f} hours.")
        
        # Peak time analysis
        hourly_patterns = self.data.groupby('hour')['shift_hours'].sum()
        if not hourly_patterns.empty:
            peak_hour = hourly_patterns.idxmax()
            summary_parts.append(f"⏰ **Peak Activity**: The busiest hour is {peak_hour}:00 with {hourly_patterns[peak_hour]:.1f} hours of activity.")
        
        # Consistency analysis
        tutor_consistency = {}
        for tutor_id in self.data['tutor_id'].unique():
            tutor_data = self.data[self.data['tutor_id'] == tutor_id]
            if len(tutor_data) > 1:
                std_dev = tutor_data['shift_hours'].std()
                mean_hours = tutor_data['shift_hours'].mean()
                consistency_score = max(0, 100 - (std_dev / mean_hours * 100)) if mean_hours > 0 else 0
                tutor_consistency[tutor_id] = consistency_score
        
        if tutor_consistency:
            avg_consistency = sum(tutor_consistency.values()) / len(tutor_consistency)
            if avg_consistency > 80:
                consistency_desc = "excellent"
            elif avg_consistency > 60:
                consistency_desc = "good"
            else:
                consistency_desc = "needs improvement"
            
            summary_parts.append(f"📈 **Consistency**: Overall consistency is {consistency_desc} with an average score of {avg_consistency:.1f}%.")
        
        # Growth trends
        if len(self.data) > 7:  # Need at least a week of data
            recent_data = self.data.tail(7)
            older_data = self.data.head(7)
            
            recent_hours = recent_data['shift_hours'].sum()
            older_hours = older_data['shift_hours'].sum()
            
            if recent_hours > older_hours * 1.1:
                summary_parts.append("🚀 **Growth Trend**: Recent activity shows strong growth compared to earlier periods.")
            elif recent_hours < older_hours * 0.9:
                summary_parts.append("📉 **Declining Trend**: Recent activity shows a decline compared to earlier periods.")
            else:
                summary_parts.append("📊 **Stable Performance**: Activity levels remain consistent over time.")
        
        # Issue identification
        issues = []
        missing_checkouts = self.data['check_out'].isna().sum()
        short_sessions = len(self.data[self.data['shift_hours'] < 1])
        
        if missing_checkouts > 0:
            issues.append(f"{missing_checkouts} missing checkouts")
        if short_sessions > 0:
            issues.append(f"{short_sessions} sessions under 1 hour")
        
        if issues:
            summary_parts.append(f"⚠️ **Areas for Improvement**: {', '.join(issues)} detected.")
        else:
            summary_parts.append("✅ **Quality**: No significant issues detected in the data.")
        
        return " ".join(summary_parts)
    
    def get_ai_recommendations(self):
        """Generate AI-powered recommendations for optimization"""
        recommendations = []
        
        if self.data.empty:
            return recommendations
        
        # 1. Staffing optimization
        current_tutors = self.data['tutor_id'].nunique()
        avg_hours_per_tutor = self.data['shift_hours'].sum() / current_tutors if current_tutors > 0 else 0
        
        if avg_hours_per_tutor < 20:
            recommendations.append({
                'type': 'staffing',
                'priority': 'high',
                'title': 'Optimize Tutor Utilization',
                'description': f'Current average of {avg_hours_per_tutor:.1f} hours per tutor suggests underutilization.',
                'action': 'Consider redistributing hours or reducing tutor count',
                'impact': 'Potential 15-25% cost savings'
            })
        
        # 2. Schedule optimization
        hourly_demand = self.data.groupby('hour')['shift_hours'].sum()
        if not hourly_demand.empty:
            peak_hour = hourly_demand.idxmax()
            low_hour = hourly_demand.idxmin()
            
            if hourly_demand[peak_hour] > hourly_demand[low_hour] * 3:
                recommendations.append({
                    'type': 'schedule',
                    'priority': 'medium',
                    'title': 'Balance Peak and Off-Peak Hours',
                    'description': f'Demand at {peak_hour}:00 is {hourly_demand[peak_hour]/hourly_demand[low_hour]:.1f}x higher than at {low_hour}:00.',
                    'action': 'Consider incentivizing off-peak shifts or adjusting capacity',
                    'impact': 'Improved resource utilization and student satisfaction'
                })
        
        # 3. Quality improvement
        short_sessions = len(self.data[self.data['shift_hours'] < 1])
        total_sessions = len(self.data)
        
        if short_sessions / total_sessions > 0.1:  # More than 10% short sessions
            recommendations.append({
                'type': 'quality',
                'priority': 'high',
                'title': 'Address Short Session Issue',
                'description': f'{short_sessions} out of {total_sessions} sessions are under 1 hour ({short_sessions/total_sessions*100:.1f}%).',
                'action': 'Review scheduling policies and minimum session requirements',
                'impact': 'Improved session quality and student outcomes'
            })
        
        # 4. Growth opportunities
        weekly_growth = self.data.groupby(self.data['check_in'].dt.isocalendar().week)['shift_hours'].sum()
        if len(weekly_growth) >= 4:
            recent_trend = weekly_growth.tail(2).pct_change().iloc[-1]
            if recent_trend > 0.1:
                recommendations.append({
                    'type': 'growth',
                    'priority': 'medium',
                    'title': 'Capitalize on Growth Momentum',
                    'description': f'Recent weekly growth of {recent_trend*100:.1f}% indicates strong demand.',
                    'action': 'Consider expanding capacity and recruiting additional tutors',
                    'impact': 'Capture market opportunity and increase revenue'
                })
        
        # 5. Consistency improvement
        daily_variance = self.data.groupby('day_of_week')['shift_hours'].sum().std()
        daily_mean = self.data.groupby('day_of_week')['shift_hours'].sum().mean()
        
        if daily_variance / daily_mean > 0.4:
            recommendations.append({
                'type': 'consistency',
                'priority': 'medium',
                'title': 'Improve Schedule Consistency',
                'description': 'High daily variation suggests inconsistent scheduling patterns.',
                'action': 'Implement standardized daily hour targets and consistent scheduling policies',
                'impact': 'Better predictability and improved student experience'
            })
        
        return recommendations
    
    def get_advanced_metrics(self):
        """Calculate advanced performance metrics"""
        if self.data.empty:
            return {}
        
        # Efficiency metrics
        total_hours = self.data['shift_hours'].sum()
        total_sessions = len(self.data)
        avg_session_length = total_hours / total_sessions if total_sessions > 0 else 0
        
        # Consistency metrics
        tutor_consistency = {}
        for tutor_id in self.data['tutor_id'].unique():
            tutor_data = self.data[self.data['tutor_id'] == tutor_id]
            if len(tutor_data) > 1:
                std_dev = tutor_data['shift_hours'].std()
                mean_hours = tutor_data['shift_hours'].mean()
                consistency_score = max(0, 100 - (std_dev / mean_hours * 100)) if mean_hours > 0 else 0
                tutor_consistency[tutor_id] = round(consistency_score, 1)
        
        # Productivity trends
        weekly_productivity = self.data.groupby(self.data['check_in'].dt.isocalendar().week).agg({
            'shift_hours': 'sum',
            'tutor_id': 'nunique'
        })
        weekly_productivity['hours_per_tutor'] = weekly_productivity['shift_hours'] / weekly_productivity['tutor_id']
        
        # Quality indicators
        session_length_distribution = {
            'short_sessions': len(self.data[self.data['shift_hours'] < 1]),
            'medium_sessions': len(self.data[(self.data['shift_hours'] >= 1) & (self.data['shift_hours'] < 3)]),
            'long_sessions': len(self.data[self.data['shift_hours'] >= 3])
        }
        
        return {
            'efficiency_score': float(round((avg_session_length / 2.5) * 100, 1)),  # Assuming 2.5h is optimal
            'consistency_scores': {str(k): float(v) for k, v in tutor_consistency.items()},
            'avg_consistency': float(round(sum(tutor_consistency.values()) / len(tutor_consistency), 1) if tutor_consistency else 0),
            'productivity_trend': [float(x) for x in weekly_productivity['hours_per_tutor'].tail(4).tolist()],
            'session_distribution': {k: int(v) for k, v in session_length_distribution.items()},
            'utilization_rate': float(round((total_hours / (self.data['tutor_id'].nunique() * 40)) * 100, 1)),  # Assuming 40h/week capacity
            'peak_efficiency_day': str(self.data.groupby('day_of_week')['shift_hours'].mean().idxmax()),
            'improvement_potential': float(round(max(0, 100 - (avg_session_length / 3.0) * 100), 1))  # Room for improvement
        }
    
    def _get_staffing_recommendations(self, optimal_tutors, current_tutors):
        """Generate staffing recommendations"""
        recommendations = []
        gap = optimal_tutors - current_tutors
        
        if gap > 2:
            recommendations.append("Urgent: Recruit 2+ additional tutors immediately")
            recommendations.append("Consider temporary staffing solutions")
        elif gap > 0:
            recommendations.append(f"Recruit {gap} additional tutor(s)")
            recommendations.append("Cross-train existing tutors for flexibility")
        elif gap < -2:
            recommendations.append("Consider reducing tutor hours or reassigning roles")
            recommendations.append("Focus on tutor development and retention")
        else:
            recommendations.append("Current staffing levels are optimal")
            recommendations.append("Focus on tutor efficiency and satisfaction")
        
        return recommendations
    
    def _get_risk_mitigation_recommendations(self, risks):
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        for risk in risks:
            if risk['type'] == 'High Dependency Risk':
                recommendations.append("Distribute key tutor's responsibilities across team")
                recommendations.append("Implement cross-training program")
            elif risk['type'] == 'Coverage Gap Risk':
                recommendations.append("Adjust schedules to cover low-activity periods")
                recommendations.append("Consider flexible staffing arrangements")
            elif risk['type'] == 'High Variability Risk':
                recommendations.append("Implement consistent scheduling policies")
                recommendations.append("Monitor and address weekly fluctuations")
            elif risk['type'] == 'Rapid Growth Risk':
                recommendations.append("Implement quality control measures")
                recommendations.append("Plan for sustainable growth trajectory")
        
        return recommendations
    
    def get_growth_data(self):
        """Get growth data for charts"""
        if self.data.empty:
            return []
        
        # Weekly growth data
        weekly_data = self.data.groupby(self.data['check_in'].dt.to_period('W')).agg({
            'shift_hours': 'sum',
            'tutor_id': 'nunique'
        }).reset_index()
        
        weekly_data['week'] = weekly_data['check_in'].astype(str)
        
        growth_data = []
        for _, row in weekly_data.iterrows():
            growth_data.append({
                'week': str(row['week']),
                'total_hours': float(row['shift_hours']),
                'active_tutors': int(row['tutor_id'])
            })
        
        return growth_data
    
    def analyze_patterns(self):
        """Analyze attendance patterns"""
        if self.data.empty:
            return {}
        
        # Average session length
        avg_session_length = self.data['shift_hours'].mean()
        
        # Most active tutor
        tutor_hours = self.data.groupby(['tutor_id', 'tutor_name'])['shift_hours'].sum()
        
        # Safely get most active tutor info
        if not tutor_hours.empty:
            try:
                most_active_idx = tutor_hours.idxmax()
                # Ensure it's a tuple (tutor_id, tutor_name)
                if isinstance(most_active_idx, tuple) and len(most_active_idx) >= 2:
                    most_active = most_active_idx
                else:
                    # Fallback: get the first tutor if index structure is unexpected
                    most_active = ('', '')
            except Exception:
                most_active = ('', '')
        else:
            most_active = ('', '')
        
        # Consistency score (how regular are the check-ins)
        tutor_consistency = {}
        for tutor_id in self.data['tutor_id'].unique():
            tutor_data = self.data[self.data['tutor_id'] == tutor_id]
            if len(tutor_data) > 1:
                # Calculate standard deviation of check-in times (hour of day)
                std_dev = tutor_data['hour'].std()
                consistency = max(0, 100 - (std_dev * 10))  # Convert to 0-100 scale
                tutor_consistency[tutor_id] = round(consistency, 1)
        
        return {
            'avg_session_length': float(round(avg_session_length, 1) if not pd.isna(avg_session_length) else 0),
            'most_active_tutor': {
                'id': str(most_active[0] if most_active and len(most_active) > 0 else ''),
                'name': str(most_active[1] if most_active and len(most_active) > 1 else ''),
                'total_hours': float(tutor_hours.max() if not tutor_hours.empty else 0)
            },
            'tutor_consistency': {str(k): float(v) for k, v in tutor_consistency.items()}
        }
    
    # ==================== CALENDAR VIEW ====================
    
    def get_session_status(self, session):
        """Determine the status of a session"""
        if pd.isna(session['check_out']):
            return 'missing_checkout'
        elif session['shift_hours'] < 1.0:
            return 'short_shift'
        elif session['shift_hours'] >= 6.0:
            return 'long_shift'
        else:
            return 'normal'
    
    def get_day_status(self, day_data):
        """Determine the overall status of a day"""
        if day_data.empty:
            return 'inactive'
        
        total_hours = day_data['shift_hours'].sum()
        has_issues = day_data['check_out'].isna().any() or (day_data['shift_hours'] < 1.0).any()
        
        if has_issues:
            return 'warning'
        elif total_hours >= 10:
            return 'high_activity'
        elif total_hours >= 5:
            return 'normal'
        else:
            return 'low_activity'
    
    def day_has_issues(self, day_data):
        """Check if a day has any issues that need attention"""
        if day_data.empty:
            return False
        
        # Check for missing checkouts
        missing_checkouts = day_data['check_out'].isna().any()
        
        # Check for very short sessions
        short_sessions = (day_data['shift_hours'] < 0.5).any()
        
        # Check for very long sessions
        long_sessions = (day_data['shift_hours'] > 12).any()
        
        return missing_checkouts or short_sessions or long_sessions

    def get_audit_logs(self, page=1, per_page=20):
        """Get paginated audit logs for admin view"""
        try:
            # Load audit logs from CSV
            audit_file = 'logs/audit_log.csv'
            if not os.path.exists(audit_file):
                # Create sample audit logs if file doesn't exist
                self._create_sample_audit_logs()
            df = pd.read_csv(audit_file)
            print(f"[DEBUG] audit_log.csv columns: {df.columns.tolist()}")
            
            # Map existing columns to expected format
            # Your audit log has: timestamp, user_email, action, details, ip_address, user_agent
            # Frontend expects: timestamp, user_email, action, details, ip_address, user_agent, user_name, admin_email, etc.
            
            # Add missing columns for frontend compatibility
            if 'user_name' not in df.columns:
                # Handle empty user_email values safely
                df['user_name'] = ''
                if 'user_email' in df.columns:
                    df['user_email'] = df['user_email'].astype(str)
                    mask = df['user_email'].notna() & (df['user_email'] != '') & (df['user_email'] != 'nan')
                    df.loc[mask, 'user_name'] = df.loc[mask, 'user_email'].str.split('@').str[0]
            if 'admin_email' not in df.columns:
                df['admin_email'] = df['user_email'] if 'user_email' in df.columns else ''
            if 'admin_user_id' not in df.columns:
                df['admin_user_id'] = ''
            if 'target_user_email' not in df.columns:
                df['target_user_email'] = ''
            if 'status' not in df.columns:
                df['status'] = 'completed'
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.sort_values('timestamp', ascending=False)
            
            total = len(df)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_df = df.iloc[start_idx:end_idx]
            
            # Convert timestamps to ISO strings for JSON serialization
            paginated_df = paginated_df.copy()  # Create a copy to avoid SettingWithCopyWarning
            paginated_df['timestamp'] = paginated_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            # Replace NaN with None for JSON serialization
            paginated_df = paginated_df.where(pd.notnull(paginated_df), None)
            logs = paginated_df.to_dict('records')
            return {'logs': logs, 'total': total}
        except Exception as e:
            import traceback
            print(f"Error loading audit logs: {e}")
            traceback.print_exc()
            return {'logs': [], 'total': 0}

    def _create_sample_audit_logs(self):
        """Create sample audit logs for testing"""
        import random
        from datetime import datetime, timedelta
        
        audit_data = []
        actions = ['login', 'logout', 'check_in', 'check_out', 'manual_entry', 'data_export']
        users = ['admin@example.com', 'manager@example.com', 'tutor1@example.com', 'tutor2@example.com']
        
        # Generate 100 sample audit entries
        for i in range(100):
            timestamp = datetime.now() - timedelta(days=random.randint(0, 30), 
                                                 hours=random.randint(0, 23),
                                                 minutes=random.randint(0, 59))
            
            action = random.choice(actions)
            user = random.choice(users)
            
            audit_data.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'user_email': user,
                'action': action,
                'details': f'Sample {action} action',
                'ip_address': f'192.168.1.{random.randint(1, 255)}',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        
        # Create directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Save to CSV
        df = pd.DataFrame(audit_data)
        df.to_csv('logs/audit_log.csv', index=False)

    def populate_audit_logs(self):
        """Populate audit logs with current data"""
        self._create_sample_audit_logs()

    def get_shifts_data(self):
        """Get shifts data for admin management"""
        try:
            # Load shifts from CSV
            shifts_file = 'logs/shifts.csv'
            if not os.path.exists(shifts_file):
                # Create sample shifts if file doesn't exist
                self._create_sample_shifts()
            
            df_shifts = pd.read_csv(shifts_file)
            
            # Load assignments
            assignments_file = 'logs/shift_assignments.csv'
            if not os.path.exists(assignments_file):
                self._create_sample_assignments()
            
            df_assignments = pd.read_csv(assignments_file)
            
            return {
                'shifts': df_shifts.to_dict('records'),
                'assignments': df_assignments.to_dict('records'),
                'tutors': self._get_available_tutors()
            }
            
        except Exception as e:
            print(f"Error loading shifts data: {e}")
            return {'shifts': [], 'assignments': [], 'tutors': []}

    def _create_sample_shifts(self):
        """Create sample shifts for testing"""
        shifts_data = [
            {
                'shift_id': 1,
                'shift_name': 'Morning Shift',
                'start_time': '08:00',
                'end_time': '12:00',
                'days_of_week': 'Monday,Tuesday,Wednesday,Thursday,Friday',
                'status': 'active'
            },
            {
                'shift_id': 2,
                'shift_name': 'Afternoon Shift',
                'start_time': '12:00',
                'end_time': '16:00',
                'days_of_week': 'Monday,Tuesday,Wednesday,Thursday,Friday',
                'status': 'active'
            },
            {
                'shift_id': 3,
                'shift_name': 'Evening Shift',
                'start_time': '16:00',
                'end_time': '20:00',
                'days_of_week': 'Monday,Tuesday,Wednesday,Thursday,Friday',
                'status': 'active'
            },
            {
                'shift_id': 4,
                'shift_name': 'Weekend Shift',
                'start_time': '10:00',
                'end_time': '18:00',
                'days_of_week': 'Saturday,Sunday',
                'status': 'active'
            }
        ]
        
        os.makedirs('logs', exist_ok=True)
        df = pd.DataFrame(shifts_data)
        df.to_csv('logs/shifts.csv', index=False)

    def _create_sample_assignments(self):
        """Create sample shift assignments for testing"""
        assignments_data = [
            {
                'assignment_id': 1,
                'shift_id': 1,
                'tutor_id': 'T001',
                'tutor_name': 'John Doe',
                'assigned_date': '2024-01-01',
                'status': 'active'
            },
            {
                'assignment_id': 2,
                'shift_id': 2,
                'tutor_id': 'T002',
                'tutor_name': 'Jane Smith',
                'assigned_date': '2024-01-01',
                'status': 'active'
            },
            {
                'assignment_id': 3,
                'shift_id': 3,
                'tutor_id': 'T003',
                'tutor_name': 'Bob Johnson',
                'assigned_date': '2024-01-01',
                'status': 'active'
            }
        ]
        
        os.makedirs('logs', exist_ok=True)
        df = pd.DataFrame(assignments_data)
        df.to_csv('logs/shift_assignments.csv', index=False)

    def _get_available_tutors(self):
        """Get list of available tutors"""
        try:
            df = self.load_data()
            if df.empty:
                return []
            
            tutors = df[['tutor_id', 'tutor_name']].drop_duplicates()
            return tutors.to_dict('records')
        except:
            return []

    def remove_shift_assignment(self, assignment_id):
        """Remove a shift assignment"""
        try:
            assignments_file = 'logs/shift_assignments.csv'
            if os.path.exists(assignments_file):
                df = pd.read_csv(assignments_file)
                df = df[df['assignment_id'] != int(assignment_id)]
                df.to_csv(assignments_file, index=False)
        except Exception as e:
            print(f"Error removing assignment: {e}")

    def deactivate_shift(self, shift_id):
        """Deactivate a shift"""
        try:
            shifts_file = 'logs/shifts.csv'
            if os.path.exists(shifts_file):
                df = pd.read_csv(shifts_file)
                df.loc[df['shift_id'] == int(shift_id), 'status'] = 'inactive'
                df.to_csv(shifts_file, index=False)
        except Exception as e:
            print(f"Error deactivating shift: {e}")

    def create_shift(self, shift_name, start_time, end_time, days_of_week):
        """Create a new shift"""
        try:
            shifts_file = 'logs/shifts.csv'
            if os.path.exists(shifts_file):
                df = pd.read_csv(shifts_file)
                new_shift_id = df['shift_id'].max() + 1 if len(df) > 0 else 1
            else:
                df = pd.DataFrame(columns=['shift_id', 'shift_name', 'start_time', 'end_time', 'days_of_week', 'status'])
                new_shift_id = 1
            
            new_shift = {
                'shift_id': new_shift_id,
                'shift_name': shift_name,
                'start_time': start_time,
                'end_time': end_time,
                'days_of_week': ','.join(days_of_week),
                'status': 'active'
            }
            
            df = pd.concat([df, pd.DataFrame([new_shift])], ignore_index=True)
            df.to_csv(shifts_file, index=False)
            
        except Exception as e:
            print(f"Error creating shift: {e}")

    def assign_shift_to_tutor(self, shift_id, tutor_id):
        """Assign a shift to a tutor"""
        try:
            assignments_file = 'logs/shift_assignments.csv'
            if os.path.exists(assignments_file):
                df = pd.read_csv(assignments_file)
                new_assignment_id = df['assignment_id'].max() + 1 if len(df) > 0 else 1
            else:
                df = pd.DataFrame(columns=['assignment_id', 'shift_id', 'tutor_id', 'tutor_name', 'assigned_date', 'status'])
                new_assignment_id = 1
            
            # Get tutor name from face log
            tutor_name = f"Tutor {tutor_id}"
            try:
                face_df = pd.read_csv('logs/face_log.csv')
                tutor_row = face_df[face_df['tutor_id'] == tutor_id]
                if not tutor_row.empty:
                    tutor_name = tutor_row['tutor_name'].iloc[0]
            except:
                pass
            
            new_assignment = {
                'assignment_id': new_assignment_id,
                'shift_id': int(shift_id),
                'tutor_id': tutor_id,
                'tutor_name': tutor_name,
                'assigned_date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'active'
            }
            
            df = pd.concat([df, pd.DataFrame([new_assignment])], ignore_index=True)
            df.to_csv(assignments_file, index=False)
            
        except Exception as e:
            print(f"Error assigning shift: {e}")

    def get_logs_for_collapsible_view(self):
        """
        Return all check-in/check-out logs as a list of dicts for the dashboard's collapsible log view.
        """
        if self.data.empty:
            return []
        logs = []
        for _, row in self.data.iterrows():
            logs.append({
                'tutor_id': row.get('tutor_id'),
                'tutor_name': row.get('tutor_name'),
                'check_in': row.get('check_in').strftime('%Y-%m-%d %H:%M') if not pd.isna(row.get('check_in')) else None,
                'check_out': row.get('check_out').strftime('%Y-%m-%d %H:%M') if not pd.isna(row.get('check_out')) else None,
                'shift_hours': float(row.get('shift_hours')) if not pd.isna(row.get('shift_hours')) else None,
                'snapshot_in': row.get('snapshot_in'),
                'snapshot_out': row.get('snapshot_out')
            })
        return logs

    def get_dashboard_summary(self):
        """
        Return a summary of KPIs for the dashboard, deduplicating logic from other methods.
        """
        if self.data.empty:
            return {
                'total_checkins': 0,
                'total_hours': 0,
                'active_tutors': 0,
                'avg_session_duration': '—',
                'avg_daily_hours': '—',
                'peak_checkin_hour': '—',
                'top_day': '—',
                'top_tutor_current_month': '—',
            }
        df = self.data.copy()
        # Remove duplicate check-ins by tutor_id and check_in time
        df = df.drop_duplicates(subset=['tutor_id', 'check_in'])
        total_checkins = len(df)
        total_hours = round(df['shift_hours'].sum(), 1)
        active_tutors = df['tutor_id'].nunique()
        avg_session_duration = round(df['shift_hours'].mean(), 2) if total_checkins > 0 else '—'
        # Daily hours
        daily_hours = df.groupby('date')['shift_hours'].sum()
        avg_daily_hours = round(daily_hours.mean(), 2) if not daily_hours.empty else '—'
        # Peak check-in hour
        if 'hour' in df.columns and not df['hour'].isna().all():
            peak_checkin_hour = int(df['hour'].mode()[0])
        else:
            peak_checkin_hour = '—'
        # Most active day
        if not daily_hours.empty:
            top_day = str(daily_hours.idxmax())
        else:
            top_day = '—'
        # Top tutor this month
        now = pd.Timestamp.now()
        month_df = df[(df['check_in'].dt.month == now.month) & (df['check_in'].dt.year == now.year)]
        if not month_df.empty:
            top_tutor_row = month_df.groupby(['tutor_id', 'tutor_name'])['shift_hours'].sum().idxmax()
            top_tutor_current_month = top_tutor_row[1] if isinstance(top_tutor_row, tuple) and len(top_tutor_row) > 1 else str(top_tutor_row)
        else:
            top_tutor_current_month = '—'
        return {
            'total_checkins': total_checkins,
            'total_hours': total_hours,
            'active_tutors': active_tutors,
            'avg_session_duration': avg_session_duration,
            'avg_daily_hours': avg_daily_hours,
            'peak_checkin_hour': peak_checkin_hour,
            'top_day': top_day,
            'top_tutor_current_month': top_tutor_current_month,
        }

    def generate_alerts(self):
        """
        Generate alerts for the dashboard based on data analysis.
        """
        alerts = []
        
        if self.data.empty:
            return alerts
        
        # Check for missing checkouts
        missing_checkouts = self.data[self.data['check_out'].isna()]
        if len(missing_checkouts) > 0:
            alerts.append({
                'type': 'warning',
                'title': 'Missing Check-outs',
                'message': f'{len(missing_checkouts)} sessions have missing check-out times'
            })
        
        # Check for very short sessions (less than 30 minutes)
        short_sessions = self.data[self.data['shift_hours'] < 0.5]
        if len(short_sessions) > 0:
            alerts.append({
                'type': 'info',
                'title': 'Short Sessions',
                'message': f'{len(short_sessions)} sessions are shorter than 30 minutes'
            })
        
        # Check for very long sessions (more than 8 hours)
        long_sessions = self.data[self.data['shift_hours'] > 8]
        if len(long_sessions) > 0:
            alerts.append({
                'type': 'warning',
                'title': 'Long Sessions',
                'message': f'{len(long_sessions)} sessions are longer than 8 hours'
            })
        
        # Check for low activity days
        daily_activity = self.data.groupby('date').size()
        low_activity_days = daily_activity[daily_activity < 3]
        if len(low_activity_days) > 0:
            alerts.append({
                'type': 'info',
                'title': 'Low Activity Days',
                'message': f'{len(low_activity_days)} days have fewer than 3 check-ins'
            })
        
        # Check for inactive tutors (no check-ins in last 7 days)
        if not self.data.empty:
            last_week = pd.Timestamp.now() - pd.Timedelta(days=7)
            recent_activity = self.data[self.data['check_in'] >= last_week]
            active_tutors = recent_activity['tutor_id'].nunique()
            total_tutors = self.data['tutor_id'].nunique()
            
            if active_tutors < total_tutors * 0.7:  # Less than 70% active
                alerts.append({
                    'type': 'warning',
                    'title': 'Low Tutor Activity',
                    'message': f'Only {active_tutors} out of {total_tutors} tutors active in the last week'
                })
        
        return alerts

    def get_session_duration_vs_checkin_hour(self):
        if self.data.empty:
            return []
        # Only include rows with valid check_in and shift_hours
        df = self.data.dropna(subset=['check_in', 'shift_hours'])
        result = []
        for _, row in df.iterrows():
            try:
                checkin_hour = pd.to_datetime(row['check_in']).hour
                duration = float(row['shift_hours'])
                result.append({'x': checkin_hour, 'y': duration})
            except Exception:
                continue
        return result

    def get_chart_data(self, dataset):
        """
        Get chart data based on the dataset type.
        """
        if self.data.empty:
            return {}
        
        try:
            if dataset == 'checkins_per_tutor':
                return self.data.groupby('tutor_name').size().to_dict()
            elif dataset == 'hours_per_tutor':
                return self.data.groupby('tutor_name')['shift_hours'].sum().to_dict()
            elif dataset == 'daily_checkins':
                # Convert date objects to strings for JSON serialization
                daily_data = self.data.groupby('date').size()
                return {str(date): int(count) for date, count in daily_data.items()}
            elif dataset == 'daily_hours':
                # Convert date objects to strings for JSON serialization
                daily_data = self.data.groupby('date')['shift_hours'].sum()
                return {str(date): float(count) for date, count in daily_data.items()}
            elif dataset == 'hourly_checkins_dist':
                # Convert hour integers to strings for JSON serialization
                hourly_data = self.data.groupby('hour').size()
                return {str(hour): int(count) for hour, count in hourly_data.items()}
            elif dataset == 'monthly_hours':
                # Convert month integers to strings for JSON serialization
                monthly_data = self.data.groupby('month')['shift_hours'].sum()
                return {str(month): float(hours) for month, hours in monthly_data.items()}
            elif dataset == 'avg_hours_per_day_of_week':
                # Convert day names to strings for JSON serialization
                daily_avg = self.data.groupby('day_of_week')['shift_hours'].mean()
                return {str(day): float(avg) for day, avg in daily_avg.items()}
            elif dataset == 'checkins_per_day_of_week':
                # Convert day names to strings for JSON serialization
                daily_counts = self.data.groupby('day_of_week').size()
                return {str(day): int(count) for day, count in daily_counts.items()}
            elif dataset == 'hourly_activity_by_day':
                # Create hourly activity heatmap data
                hourly_by_day = self.data.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
                return {str(day): {str(hour): int(count) for hour, count in day_data.items()} 
                       for day, day_data in hourly_by_day.items()}
            elif dataset == 'session_duration_distribution':
                # Create session duration distribution
                duration_ranges = pd.cut(self.data['shift_hours'], 
                                       bins=[0, 1, 2, 4, 6, 8, float('inf')], 
                                       labels=['0-1h', '1-2h', '2-4h', '4-6h', '6-8h', '8h+'])
                duration_counts = duration_ranges.value_counts()
                return {str(range_name): int(count) for range_name, count in duration_counts.items()}
            elif dataset == 'punctuality_analysis':
                # Enhanced punctuality analysis using real data
                df = self.data.copy()
                if df.empty or 'check_in' not in df or 'expected_check_in' not in df:
                    return {
                        'breakdown': {'Early': 0, 'On Time': 0, 'Late': 0},
                        'trends': {},
                        'day_time': {},
                        'outliers': {'most_punctual': [], 'least_punctual': []},
                        'deviation_distribution': {}
                    }
                # Calculate deviation in minutes
                df['deviation'] = (pd.to_datetime(df['check_in']) - pd.to_datetime(df['expected_check_in'])).dt.total_seconds() / 60
                # Categorize
                def categorize(dev):
                    if pd.isna(dev):
                        return 'On Time'
                    if dev < -5:
                        return 'Early'
                    elif dev > 5:
                        return 'Late'
                    else:
                        return 'On Time'
                df['punctuality'] = df['deviation'].apply(categorize)
                # Breakdown
                breakdown_counts = df['punctuality'].value_counts().to_dict()
                total = len(df)
                breakdown = {}
                for cat in ['Early', 'On Time', 'Late']:
                    count = breakdown_counts.get(cat, 0)
                    percent = round(count / total * 100, 1) if total else 0
                    avg_dev = df[df['punctuality'] == cat]['deviation'].mean()
                    if pd.isna(avg_dev):
                        avg_dev_str = '-'
                    else:
                        avg_dev_str = f"{avg_dev:+.0f} min" if cat != 'On Time' else f"±{abs(avg_dev):.0f} min"
                    breakdown[cat] = {
                        'count': count,
                        'percent': percent,
                        'avg_deviation': avg_dev_str
                    }
                # Trends (by day)
                df['day'] = pd.to_datetime(df['check_in']).dt.day_name()
                trends = {}
                for cat in ['Early', 'On Time', 'Late']:
                    trends[cat] = df[df['punctuality'] == cat].groupby('day').size().reindex([
                        'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'
                    ], fill_value=0).tolist()
                # Day-of-week & time-of-day
                df['hour'] = pd.to_datetime(df['check_in']).dt.hour
                def time_slot(h):
                    if 5 <= h < 12: return 'Morning'
                    if 12 <= h < 17: return 'Afternoon'
                    return 'Evening'
                df['time_slot'] = df['hour'].apply(time_slot)
                day_time = {}
                for slot in ['Morning', 'Afternoon', 'Evening']:
                    slot_counts = df[df['time_slot'] == slot].groupby('day').size().reindex([
                        'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'
                    ], fill_value=0).tolist()
                    day_time[slot] = slot_counts
                # Outliers (top/least punctual by avg deviation)
                tutor_dev = df.groupby('tutor_name')['deviation'].mean().sort_values()
                most_punctual = tutor_dev.abs().sort_values().head(3).index.tolist()
                least_punctual = tutor_dev.abs().sort_values(ascending=False).head(3).index.tolist()
                # Deviation distribution
                bins = [-float('inf'), -15, -5, 5, 15, float('inf')]
                labels = ['Early >15min', 'Early 5-15min', 'On Time ±5min', 'Late 5-15min', 'Late >15min']
                df['dev_bucket'] = pd.cut(df['deviation'], bins=bins, labels=labels)
                dev_dist = df['dev_bucket'].value_counts().reindex(labels, fill_value=0).to_dict()
                return {
                    'breakdown': breakdown,
                    'trends': trends,
                    'day_time': day_time,
                    'outliers': {
                        'most_punctual': most_punctual,
                        'least_punctual': least_punctual
                    },
                    'deviation_distribution': dev_dist
                }
            elif dataset == 'avg_session_duration_per_tutor':
                # Average session duration per tutor
                avg_duration = self.data.groupby('tutor_name')['shift_hours'].mean()
                return {str(tutor): float(duration) for tutor, duration in avg_duration.items()}
            elif dataset == 'tutor_consistency_score':
                # Calculate consistency score based on regular check-ins
                tutor_consistency = {}
                for tutor_name in self.data['tutor_name'].unique():
                    tutor_data = self.data[self.data['tutor_name'] == tutor_name]
                    if len(tutor_data) > 1:
                        # Calculate variance in session durations as consistency measure
                        variance = tutor_data['shift_hours'].var()
                        # Convert to a 0-100 score (lower variance = higher consistency)
                        max_variance = 4.0  # Assume max variance of 4 hours
                        consistency_score = max(0, 100 - (variance / max_variance * 100))
                        tutor_consistency[str(tutor_name)] = float(consistency_score)
                    else:
                        tutor_consistency[str(tutor_name)] = 50.0  # Default score for single session
                return tutor_consistency
            elif dataset == 'cumulative_checkins':
                # Cumulative check-ins over time
                daily_checkins = self.data.groupby('date').size()
                cumulative = daily_checkins.cumsum()
                return {str(date): int(count) for date, count in cumulative.items()}
            elif dataset == 'cumulative_hours':
                # Cumulative hours over time
                daily_hours = self.data.groupby('date')['shift_hours'].sum()
                cumulative = daily_hours.cumsum()
                return {str(date): float(hours) for date, hours in cumulative.items()}
            elif dataset == 'session_duration_vs_checkin_hour':
                return self.get_session_duration_vs_checkin_hour()
            else:
                return {}
        except Exception as e:
            logging.error(f"Error in get_chart_data for dataset '{dataset}': {e}")
            return {}

    def get_all_logs(self):
        """
        Get all logs in a format suitable for the frontend.
        """
        if self.data.empty:
            return []
        
        logs = []
        for _, row in self.data.iterrows():
            logs.append({
                'tutor_id': row.get('tutor_id'),
                'tutor_name': row.get('tutor_name'),
                'check_in': row.get('check_in').strftime('%Y-%m-%d %H:%M') if not pd.isna(row.get('check_in')) else None,
                'check_out': row.get('check_out').strftime('%Y-%m-%d %H:%M') if not pd.isna(row.get('check_out')) else None,
                'shift_hours': float(row.get('shift_hours')) if not pd.isna(row.get('shift_hours')) else None,
                'snapshot_in': row.get('snapshot_in'),
                'snapshot_out': row.get('snapshot_out')
            })
        
        return logs

    def log_admin_action(self, action, target_user_email=None, details=""):
        """Log admin actions for audit trail"""
        from flask import request, session
        from datetime import datetime
        import os
        import pandas as pd
        try:
            # Try to get current user from session
            current_user = session.get('user')
            if not current_user:
                return
            audit_file = 'logs/audit_log.csv'
            os.makedirs(os.path.dirname(audit_file), exist_ok=True)
            audit_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'admin_email': current_user.get('email', 'unknown'),
                'action': action,
                'target_user_email': target_user_email or '',
                'details': details,
                'ip_address': request.remote_addr if request else '',
                'user_agent': request.headers.get('User-Agent', '') if request else ''
            }
            # Load existing audit log or create new one
            if os.path.exists(audit_file):
                audit_df = pd.read_csv(audit_file)
            else:
                audit_df = pd.DataFrame(columns=[
                    'timestamp', 'admin_email', 'action', 'target_user_email', 
                    'details', 'ip_address', 'user_agent'
                ])
            audit_df = pd.concat([audit_df, pd.DataFrame([audit_entry])], ignore_index=True)
            audit_df.to_csv(audit_file, index=False)
        except Exception as e:
            print(f"Error logging admin action: {e}")

# Global instance
analytics = TutorAnalytics()