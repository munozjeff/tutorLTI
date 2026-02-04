"""
Simple in-memory database models for the LTI Tutor
Compatible with Python 3.14
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid

# In-memory storage
_users = {}
_sessions = {}
_messages = {}
_quiz_responses = {}
_analytics = {}


class User:
    """User model for storing LTI user information"""
    
    def __init__(self, lti_user_id: str, email: str = None, name: str = None, role: str = 'student'):
        self.id = str(uuid.uuid4())
        self.lti_user_id = lti_user_id
        self.email = email
        self.name = name
        self.role = role
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'lti_user_id': self.lti_user_id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def save(self):
        self.updated_at = datetime.utcnow()
        _users[self.lti_user_id] = self
        return self
    
    @staticmethod
    def get_by_lti_id(lti_user_id: str):
        return _users.get(lti_user_id)
    
    @staticmethod
    def get_by_id(user_id: str):
        for user in _users.values():
            if user.id == user_id:
                return user
        return None


class TutorSession:
    """Tutor conversation sessions"""
    
    def __init__(self, user_id: str, context_id: str = None, resource_id: str = None, topic: str = None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.context_id = context_id
        self.resource_id = resource_id
        self.topic = topic
        self.started_at = datetime.utcnow()
        self.ended_at = None
    
    def to_dict(self):
        messages = Message.get_by_session(self.id)
        return {
            'id': self.id,
            'user_id': self.user_id,
            'context_id': self.context_id,
            'resource_id': self.resource_id,
            'topic': self.topic,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'messages': [m.to_dict() for m in messages]
        }
    
    def save(self):
        _sessions[self.id] = self
        return self
    
    @staticmethod
    def get_by_id(session_id: str):
        return _sessions.get(session_id)
    
    @staticmethod
    def get_by_user(user_id: str, limit: int = 20):
        sessions = [s for s in _sessions.values() if s.user_id == user_id]
        sessions.sort(key=lambda x: x.started_at, reverse=True)
        return sessions[:limit]


class Message:
    """Chat messages in tutor sessions"""
    
    def __init__(self, session_id: str, role: str, content: str, message_type: str = 'chat'):
        self.id = str(uuid.uuid4())
        self.session_id = session_id
        self.role = role
        self.content = content
        self.message_type = message_type
        self.created_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'message_type': self.message_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def save(self):
        if self.session_id not in _messages:
            _messages[self.session_id] = []
        _messages[self.session_id].append(self)
        return self
    
    @staticmethod
    def get_by_session(session_id: str):
        return _messages.get(session_id, [])


class QuizResponse:
    """Student quiz/exam responses for analysis"""
    
    def __init__(self, user_id: str, question_id: str, student_answer: str, **kwargs):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.context_id = kwargs.get('context_id')
        self.question_id = question_id
        self.question_text = kwargs.get('question_text')
        self.student_answer = student_answer
        self.correct_answer = kwargs.get('correct_answer')
        self.is_correct = kwargs.get('is_correct')
        self.ai_feedback = kwargs.get('ai_feedback')
        self.score = kwargs.get('score')
        self.created_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'question_text': self.question_text,
            'student_answer': self.student_answer,
            'is_correct': self.is_correct,
            'ai_feedback': self.ai_feedback,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def save(self):
        if self.user_id not in _quiz_responses:
            _quiz_responses[self.user_id] = []
        _quiz_responses[self.user_id].append(self)
        return self
    
    @staticmethod
    def get_by_user(user_id: str, limit: int = 20):
        responses = _quiz_responses.get(user_id, [])
        responses.sort(key=lambda x: x.created_at, reverse=True)
        return responses[:limit]


class LearningAnalytics:
    """Analytics for predictive tutoring"""
    
    def __init__(self, user_id: str, context_id: str = None, topic: str = None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.context_id = context_id
        self.topic = topic
        self.total_attempts = 0
        self.correct_attempts = 0
        self.average_score = 0.0
        self.total_time_spent = 0
        self.last_activity = datetime.utcnow()
        self.predicted_performance = None
        self.difficulty_level = 'medium'
        self.needs_intervention = False
        self.intervention_reason = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic': self.topic,
            'total_attempts': self.total_attempts,
            'correct_attempts': self.correct_attempts,
            'average_score': self.average_score,
            'predicted_performance': self.predicted_performance,
            'difficulty_level': self.difficulty_level,
            'needs_intervention': self.needs_intervention,
            'intervention_reason': self.intervention_reason
        }
    
    def save(self):
        self.updated_at = datetime.utcnow()
        key = f"{self.user_id}:{self.context_id}:{self.topic}"
        _analytics[key] = self
        return self
    
    @staticmethod
    def get_or_create(user_id: str, context_id: str, topic: str):
        key = f"{user_id}:{context_id}:{topic}"
        if key not in _analytics:
            analytics = LearningAnalytics(user_id, context_id, topic)
            analytics.save()
        return _analytics[key]
    
    @staticmethod
    def get_by_user(user_id: str, context_id: str = None):
        result = []
        for key, analytics in _analytics.items():
            if analytics.user_id == user_id:
                if context_id is None or analytics.context_id == context_id:
                    result.append(analytics)
        return result
