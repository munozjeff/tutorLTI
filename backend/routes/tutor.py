"""
Tutor API Routes - Handles chat and tutoring functionality
"""
from flask import Blueprint, request, jsonify, session

from models import TutorSession, Message, QuizResponse, User
from services.ai_tutor import ai_tutor
from services.analytics import analytics_service

tutor_bp = Blueprint('tutor', __name__, url_prefix='/api/tutor')


def get_current_user():
    """Get current user from session"""
    lti_user = session.get('lti_user')
    if not lti_user:
        return None
    return User.get_by_id(lti_user.get('id'))


@tutor_bp.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint for tutor interactions"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    user_message = data['message']
    session_id = data.get('session_id')
    topic = data.get('topic', 'General')
    
    user = get_current_user()
    lti_context = session.get('lti_context', {})
    
    tutor_session = None
    if session_id:
        tutor_session = TutorSession.get_by_id(session_id)
    
    if not tutor_session and user:
        tutor_session = TutorSession(
            user_id=user.id,
            context_id=lti_context.get('context_id'),
            resource_id=lti_context.get('resource_id'),
            topic=topic
        )
        tutor_session.save()
    
    conversation_history = []
    if tutor_session:
        messages = Message.get_by_session(tutor_session.id)
        conversation_history = [
            {'role': m.role, 'content': m.content}
            for m in messages[-10:]
        ]
    
    context = {
        'topic': topic,
        'course_info': lti_context.get('context_title', '')
    }
    
    if user:
        student_profile = analytics_service.get_student_profile(
            user.id, 
            lti_context.get('context_id')
        )
        context['student_level'] = student_profile.get('recommended_difficulty', 'medium')
        
        if student_profile.get('needs_intervention'):
            predictive_hint = ai_tutor.get_predictive_hint(
                topic,
                student_profile,
                user_message
            )
            if predictive_hint:
                context['predictive_hint'] = predictive_hint
    
    ai_response = ai_tutor.get_response(
        user_message,
        conversation_history,
        context
    )
    
    if tutor_session:
        user_msg = Message(
            session_id=tutor_session.id,
            role='user',
            content=user_message,
            message_type='chat'
        )
        user_msg.save()
        
        assistant_msg = Message(
            session_id=tutor_session.id,
            role='assistant',
            content=ai_response,
            message_type='chat'
        )
        assistant_msg.save()
    
    response_data = {
        'response': ai_response,
        'session_id': tutor_session.id if tutor_session else None
    }
    
    if 'predictive_hint' in context:
        response_data['predictive_hint'] = context['predictive_hint']
    
    return jsonify(response_data)


@tutor_bp.route('/analyze-answer', methods=['POST'])
def analyze_answer():
    """Analyze a student's answer and provide feedback"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Data is required'}), 400
    
    question = data.get('question', '')
    student_answer = data.get('student_answer', '')
    correct_answer = data.get('correct_answer')
    question_id = data.get('question_id', 'unknown')
    
    if not question or not student_answer:
        return jsonify({'error': 'Question and student_answer are required'}), 400
    
    lti_context = session.get('lti_context', {})
    
    analysis = ai_tutor.analyze_answer(
        question,
        student_answer,
        correct_answer
    )
    
    user = get_current_user()
    if user:
        quiz_response = QuizResponse(
            user_id=user.id,
            question_id=question_id,
            student_answer=student_answer,
            context_id=lti_context.get('context_id'),
            question_text=question,
            correct_answer=correct_answer,
            is_correct=analysis.get('is_correct', False),
            ai_feedback=analysis.get('feedback', ''),
            score=analysis.get('score', 0)
        )
        quiz_response.save()
        
        topic = data.get('topic', 'General')
        analytics_service.update_analytics(
            user.id,
            lti_context.get('context_id', 'default'),
            topic,
            analysis.get('score', 0)
        )
    
    return jsonify(analysis)


@tutor_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """Get user's tutor sessions"""
    user = get_current_user()
    if not user:
        return jsonify({'sessions': []})
    
    sessions = TutorSession.get_by_user(user.id)
    return jsonify({
        'sessions': [s.to_dict() for s in sessions]
    })


@tutor_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session_messages(session_id):
    """Get messages from a specific session"""
    user = get_current_user()
    
    tutor_session = TutorSession.get_by_id(session_id)
    if not tutor_session:
        return jsonify({'error': 'Session not found'}), 404
    
    if user and tutor_session.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(tutor_session.to_dict())


@tutor_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get student's learning analytics"""
    user = get_current_user()
    if not user:
        # Return demo data for unauthenticated users
        return jsonify({
            'profile': {
                'overall_performance': 75.0,
                'strong_topics': ['Matemáticas básicas'],
                'weak_areas': [],
                'learning_velocity': 'normal',
                'needs_intervention': False,
                'recommended_difficulty': 'medium',
                'total_topics_studied': 3,
                'topics_mastered': 1
            },
            'interventions': [],
            'quiz_history': []
        })
    
    lti_context = session.get('lti_context', {})
    context_id = request.args.get('context_id', lti_context.get('context_id'))
    
    profile = analytics_service.get_student_profile(user.id, context_id)
    interventions = analytics_service.get_intervention_suggestions(user.id, context_id)
    quiz_history = analytics_service.get_quiz_history(user.id)
    
    return jsonify({
        'profile': profile,
        'interventions': interventions,
        'quiz_history': quiz_history
    })


@tutor_bp.route('/hint', methods=['POST'])
def get_predictive_hint():
    """Get a predictive hint for a specific topic/question"""
    data = request.get_json()
    topic = data.get('topic', 'General')
    current_question = data.get('question')
    
    user = get_current_user()
    if not user:
        return jsonify({'hint': None})
    
    lti_context = session.get('lti_context', {})
    student_profile = analytics_service.get_student_profile(
        user.id,
        lti_context.get('context_id')
    )
    
    hint = ai_tutor.get_predictive_hint(
        topic,
        student_profile,
        current_question
    )
    
    return jsonify({'hint': hint})
