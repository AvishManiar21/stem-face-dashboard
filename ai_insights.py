#!/usr/bin/env python3
"""
AI Insights module for tutor dashboard
Handles AI-generated insights, recommendations, and analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIInsights:
    """
    AI-powered insights and recommendations for tutor dashboard.
    Provides natural language analysis and actionable recommendations.
    """
    
    def __init__(self, face_log_file='logs/face_log_with_expected.csv', max_date=None):
        self.face_log_file = face_log_file
        self.max_date = max_date or pd.Timestamp.now().normalize()
        self.data = self.load_data()
        
    def load_data(self):
        """Load and preprocess face log data for AI analysis"""
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
            
            return df.sort_values('check_in')
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading AI insights data: {e}")
            return pd.DataFrame()
    
    def generate_nlp_summary(self):
        """Generate natural language summary of performance"""
        if self.data.empty:
            return "No data available for analysis."
        
        try:
            # Calculate key metrics
            total_sessions = len(self.data)
            total_hours = self.data['shift_hours'].sum()
            avg_session_length = self.data['shift_hours'].mean()
            unique_tutors = self.data['tutor_id'].nunique()
            
            # Time period analysis
            date_range = self.data['date'].max() - self.data['date'].min()
            days_analyzed = date_range.days + 1
            
            # Performance trends
            daily_hours = self.data.groupby('date')['shift_hours'].sum()
            if len(daily_hours) >= 7:
                recent_avg = daily_hours.tail(7).mean()
                overall_avg = daily_hours.mean()
                trend = "increasing" if recent_avg > overall_avg else "decreasing" if recent_avg < overall_avg else "stable"
            else:
                trend = "insufficient data"
            
            # Busiest patterns
            busiest_day = self.data.groupby('day_of_week').size().idxmax()
            busiest_hour = self.data.groupby('hour').size().idxmax()
            
            # Generate summary
            summary = f"""
            Over the past {days_analyzed} days, {unique_tutors} tutors completed {total_sessions} sessions totaling {total_hours:.1f} hours. 
            The average session length is {avg_session_length:.1f} hours, and recent activity shows a {trend} trend. 
            {busiest_day} is the busiest day, with peak activity around {busiest_hour}:00.
            """
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating NLP summary: {e}")
            return "Unable to generate performance summary due to data processing error."
    
    def generate_recommendations(self):
        """Generate AI-powered recommendations"""
        if self.data.empty:
            return []
        
        try:
            recommendations = []
            
            # Analyze session patterns
            daily_hours = self.data.groupby('date')['shift_hours'].sum()
            avg_daily_hours = daily_hours.mean()
            
            # Recommendation 1: Staffing optimization
            if avg_daily_hours > 20:
                recommendations.append({
                    'type': 'staffing',
                    'priority': 'high',
                    'title': 'High Daily Hours - Consider Additional Staffing',
                    'description': f'Average daily hours ({avg_daily_hours:.1f}h) suggest high demand.',
                    'action': 'Review staffing levels and consider hiring additional tutors',
                    'impact': 'Reduce tutor workload and improve service quality'
                })
            elif avg_daily_hours < 8:
                recommendations.append({
                    'type': 'staffing',
                    'priority': 'medium',
                    'title': 'Low Daily Hours - Optimize Staffing',
                    'description': f'Average daily hours ({avg_daily_hours:.1f}h) suggest underutilization.',
                    'action': 'Review scheduling and consider reducing shifts',
                    'impact': 'Reduce operational costs and improve efficiency'
                })
            
            # Recommendation 2: Schedule optimization
            day_distribution = self.data.groupby('day_of_week').size()
            if len(day_distribution) > 0:
                busiest_day = day_distribution.idxmax()
                slowest_day = day_distribution.idxmin()
                busiest_count = day_distribution.max()
                slowest_count = day_distribution.min()
                
                if busiest_count > slowest_count * 2:
                    recommendations.append({
                        'type': 'schedule',
                        'priority': 'medium',
                        'title': 'Uneven Day Distribution',
                        'description': f'{busiest_day} has {busiest_count} sessions vs {slowest_day} with {slowest_count}.',
                        'action': 'Redistribute sessions or offer incentives for slower days',
                        'impact': 'Better resource utilization and improved service availability'
                    })
            
            # Recommendation 3: Session length optimization
            session_lengths = self.data['shift_hours']
            short_sessions = session_lengths[session_lengths < 1.0]
            long_sessions = session_lengths[session_lengths > 6.0]
            
            if len(short_sessions) > len(self.data) * 0.2:
                recommendations.append({
                    'type': 'quality',
                    'priority': 'medium',
                    'title': 'High Number of Short Sessions',
                    'description': f'{len(short_sessions)} sessions under 1 hour detected.',
                    'action': 'Review session scheduling and minimum duration policies',
                    'impact': 'Improve session quality and tutor effectiveness'
                })
            
            if len(long_sessions) > len(self.data) * 0.1:
                recommendations.append({
                    'type': 'quality',
                    'priority': 'low',
                    'title': 'Long Sessions Detected',
                    'description': f'{len(long_sessions)} sessions over 6 hours detected.',
                    'action': 'Monitor tutor fatigue and consider break policies',
                    'impact': 'Maintain tutor well-being and service quality'
                })
            
            # Recommendation 4: Growth opportunities
            if len(self.data) > 0:
                recent_weeks = self.data.groupby('week').size().tail(4)
                if len(recent_weeks) >= 2:
                    growth_rate = (recent_weeks.iloc[-1] - recent_weeks.iloc[0]) / recent_weeks.iloc[0] * 100
                    
                    if growth_rate > 20:
                        recommendations.append({
                            'type': 'growth',
                            'priority': 'high',
                            'title': 'Strong Growth Trend',
                            'description': f'{growth_rate:.1f}% growth in sessions over recent weeks.',
                            'action': 'Consider expanding capacity and hiring additional tutors',
                            'impact': 'Capitalize on growth momentum and meet increasing demand'
                        })
                    elif growth_rate < -10:
                        recommendations.append({
                            'type': 'growth',
                            'priority': 'high',
                            'title': 'Declining Activity',
                            'description': f'{abs(growth_rate):.1f}% decline in sessions over recent weeks.',
                            'action': 'Investigate causes and implement retention strategies',
                            'impact': 'Reverse decline and stabilize operations'
                        })
            
            # Recommendation 5: Consistency improvement
            if len(daily_hours) >= 7:
                daily_variance = daily_hours.var()
                if daily_variance > avg_daily_hours * 0.5:
                    recommendations.append({
                        'type': 'consistency',
                        'priority': 'medium',
                        'title': 'High Daily Variability',
                        'description': 'Significant day-to-day variation in hours.',
                        'action': 'Implement more consistent scheduling patterns',
                        'impact': 'Improve predictability and resource planning'
                    })
            
            return recommendations[:5]  # Limit to top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def calculate_confidence_score(self):
        """Calculate AI confidence score based on data quality and patterns"""
        if self.data.empty:
            return 0
        
        try:
            score = 0
            
            # Data volume (0-30 points)
            total_records = len(self.data)
            if total_records >= 100:
                score += 30
            elif total_records >= 50:
                score += 20
            elif total_records >= 20:
                score += 10
            
            # Data consistency (0-25 points)
            if total_records > 0:
                missing_checkouts = self.data['check_out'].isna().sum()
                consistency_ratio = 1 - (missing_checkouts / total_records)
                score += consistency_ratio * 25
            
            # Time span (0-25 points)
            if len(self.data) > 0:
                date_range = self.data['date'].max() - self.data['date'].min()
                days_span = date_range.days
                if days_span >= 30:
                    score += 25
                elif days_span >= 14:
                    score += 15
                elif days_span >= 7:
                    score += 10
            
            # Pattern consistency (0-20 points)
            if len(self.data) >= 7:
                daily_hours = self.data.groupby('date')['shift_hours'].sum()
                if len(daily_hours) >= 7:
                    variance = daily_hours.var()
                    mean_hours = daily_hours.mean()
                    if mean_hours > 0:
                        cv = variance / mean_hours
                        if cv < 0.5:
                            score += 20
                        elif cv < 1.0:
                            score += 15
                        elif cv < 2.0:
                            score += 10
            
            return min(100, max(0, round(score)))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0
    
    def calculate_forecast_accuracy(self):
        """Calculate accuracy of previous forecasts (placeholder)"""
        # This would compare previous forecasts with actual data
        # For now, return a placeholder value
        return 85.5  # Placeholder accuracy percentage
    
    def get_growth_opportunities(self):
        """Identify top growth opportunities"""
        if self.data.empty:
            return []
        
        try:
            opportunities = []
            
            # Analyze day-of-week opportunities
            day_analysis = self.data.groupby('day_of_week').agg({
                'shift_hours': ['sum', 'mean', 'count']
            }).round(1)
            
            # Find days with high average hours but low frequency
            for day in day_analysis.index:
                avg_hours = day_analysis.loc[day, ('shift_hours', 'mean')]
                count = day_analysis.loc[day, ('shift_hours', 'count')]
                
                if avg_hours > 3.0 and count < 10:  # High value, low frequency
                    opportunities.append(f"{day}: High-value sessions ({avg_hours}h avg)")
            
            # Analyze hourly opportunities
            hour_analysis = self.data.groupby('hour').agg({
                'shift_hours': ['sum', 'mean', 'count']
            }).round(1)
            
            # Find hours with high average hours but low frequency
            for hour in hour_analysis.index:
                avg_hours = hour_analysis.loc[hour, ('shift_hours', 'mean')]
                count = hour_analysis.loc[hour, ('shift_hours', 'count')]
                
                if avg_hours > 2.5 and count < 15:  # High value, low frequency
                    opportunities.append(f"{hour}:00: Productive time slots ({avg_hours}h avg)")
            
            return opportunities[:3]  # Return top 3 opportunities
            
        except Exception as e:
            logger.error(f"Error identifying growth opportunities: {e}")
            return []
    
    def get_insights_summary(self):
        """Get comprehensive AI insights summary"""
        try:
            nlp_summary = self.generate_nlp_summary()
            recommendations = self.generate_recommendations()
            confidence_score = self.calculate_confidence_score()
            forecast_accuracy = self.calculate_forecast_accuracy()
            growth_opportunities = self.get_growth_opportunities()
            
            return {
                'nlp_summary': nlp_summary,
                'ai_recommendations': recommendations,
                'confidence_score': confidence_score,
                'forecast_accuracy': forecast_accuracy,
                'growth_opportunities': growth_opportunities,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error in insights summary: {e}")
            return {
                'nlp_summary': 'Unable to generate insights due to processing error.',
                'ai_recommendations': [],
                'confidence_score': 0,
                'forecast_accuracy': 0,
                'growth_opportunities': [],
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            } 