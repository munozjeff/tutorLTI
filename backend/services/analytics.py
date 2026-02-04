"""
Learning Analytics Service - Predictive analysis for student performance
"""
from datetime import datetime
from typing import Dict, List
from models import LearningAnalytics, QuizResponse, User


class AnalyticsService:
    """Service for learning analytics and predictions"""
    
    @staticmethod
    def update_analytics(user_id: str, context_id: str, topic: str, 
                        score: float, time_spent: int = 0) -> LearningAnalytics:
        """Update learning analytics after a student interaction"""
        analytics = LearningAnalytics.get_or_create(user_id, context_id, topic)
        
        # Update metrics
        analytics.total_attempts += 1
        if score >= 70:
            analytics.correct_attempts += 1
        
        # Calculate new average
        old_total = analytics.average_score * (analytics.total_attempts - 1)
        analytics.average_score = (old_total + score) / analytics.total_attempts
        
        # Update time
        analytics.total_time_spent += time_spent
        analytics.last_activity = datetime.utcnow()
        
        # Update predictions
        analytics.predicted_performance = AnalyticsService._predict_performance(analytics)
        analytics.difficulty_level = AnalyticsService._calculate_difficulty(analytics)
        analytics.needs_intervention = AnalyticsService._check_intervention_needed(analytics)
        
        if analytics.needs_intervention:
            analytics.intervention_reason = AnalyticsService._get_intervention_reason(analytics)
        
        analytics.save()
        return analytics
    
    @staticmethod
    def get_student_profile(user_id: str, context_id: str = None) -> Dict:
        """Get comprehensive student profile for predictive tutoring"""
        analytics_list = LearningAnalytics.get_by_user(user_id, context_id)
        
        if not analytics_list:
            return {
                'overall_performance': 50.0,
                'strong_topics': [],
                'weak_areas': [],
                'learning_velocity': 'normal',
                'needs_intervention': False,
                'recommended_difficulty': 'medium',
                'total_topics_studied': 0,
                'topics_mastered': 0
            }
        
        total_score = sum(a.average_score for a in analytics_list)
        overall_performance = total_score / len(analytics_list)
        
        strong_topics = [a.topic for a in analytics_list if a.average_score >= 80]
        weak_areas = [a.topic for a in analytics_list if a.average_score < 60]
        needs_intervention = any(a.needs_intervention for a in analytics_list)
        
        if overall_performance >= 85:
            recommended_difficulty = 'hard'
        elif overall_performance >= 60:
            recommended_difficulty = 'medium'
        else:
            recommended_difficulty = 'easy'
        
        return {
            'overall_performance': round(overall_performance, 2),
            'strong_topics': strong_topics,
            'weak_areas': weak_areas,
            'learning_velocity': 'normal',
            'needs_intervention': needs_intervention,
            'recommended_difficulty': recommended_difficulty,
            'total_topics_studied': len(analytics_list),
            'topics_mastered': len([a for a in analytics_list if a.average_score >= 90])
        }
    
    @staticmethod
    def get_intervention_suggestions(user_id: str, context_id: str = None) -> List[Dict]:
        """Get proactive intervention suggestions for a student"""
        analytics_list = LearningAnalytics.get_by_user(user_id, context_id)
        interventions = [a for a in analytics_list if a.needs_intervention]
        
        suggestions = []
        for i in interventions:
            suggestions.append({
                'topic': i.topic,
                'current_score': i.average_score,
                'reason': i.intervention_reason,
                'priority': 'high' if i.average_score < 40 else 'medium',
                'suggested_actions': AnalyticsService._get_suggested_actions(i)
            })
        
        suggestions.sort(key=lambda x: x['current_score'])
        return suggestions
    
    @staticmethod
    def get_quiz_history(user_id: str, limit: int = 20) -> List[Dict]:
        """Get recent quiz response history for a student"""
        responses = QuizResponse.get_by_user(user_id, limit)
        return [r.to_dict() for r in responses]
    
    @staticmethod
    def _predict_performance(analytics: LearningAnalytics) -> float:
        """Predict future performance based on historical data"""
        if analytics.total_attempts < 3:
            return analytics.average_score
        
        if analytics.correct_attempts / analytics.total_attempts > 0.6:
            trend_factor = 1.05
        elif analytics.correct_attempts / analytics.total_attempts < 0.4:
            trend_factor = 0.95
        else:
            trend_factor = 1.0
        
        predicted = analytics.average_score * 0.7 + 50 * 0.3
        predicted *= trend_factor
        
        return min(100, max(0, predicted))
    
    @staticmethod
    def _calculate_difficulty(analytics: LearningAnalytics) -> str:
        if analytics.average_score >= 85:
            return 'hard'
        elif analytics.average_score >= 60:
            return 'medium'
        else:
            return 'easy'
    
    @staticmethod
    def _check_intervention_needed(analytics: LearningAnalytics) -> bool:
        if analytics.average_score < 50:
            return True
        if analytics.predicted_performance and \
           analytics.predicted_performance < analytics.average_score - 10:
            return True
        return False
    
    @staticmethod
    def _get_intervention_reason(analytics: LearningAnalytics) -> str:
        if analytics.average_score < 40:
            return "Puntuación muy baja - necesita apoyo inmediato"
        elif analytics.average_score < 50:
            return "Puntuación por debajo del promedio - requiere refuerzo"
        else:
            return "Requiere seguimiento y apoyo adicional"
    
    @staticmethod
    def _get_suggested_actions(analytics: LearningAnalytics) -> List[str]:
        actions = []
        if analytics.average_score < 40:
            actions.append("Revisar conceptos fundamentales del tema")
            actions.append("Practicar con ejercicios de nivel básico")
        elif analytics.average_score < 60:
            actions.append("Repasar material del curso")
            actions.append("Completar ejercicios adicionales")
        actions.append("Consultar con el tutor virtual para aclarar dudas")
        return actions


analytics_service = AnalyticsService()
