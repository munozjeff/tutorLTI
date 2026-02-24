"""
Tutor API Routes - Handles chat and tutoring functionality
"""
from flask import Blueprint, request, jsonify, session

from models import TutorSession, Message, QuizResponse, User
from services.analytics import analytics_service
from services.llm_factory import LLMFactory
import services.memory_service as memory_service

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
    lti_user_data = session.get('lti_user', {})
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
    
    # Build enhanced context with ALL LTI data
    context = {
        'topic': topic,
        'user_name': lti_user_data.get('name', 'Estudiante'),
        'user_email': lti_user_data.get('email', ''),
        'user_role': lti_user_data.get('role', 'student'),
        'course_name': lti_context.get('context_title', ''),
        'course_id': lti_context.get('context_id', ''),
        'resource_title': lti_context.get('resource_title', ''),
        'course_info': lti_context.get('context_title', '')
    }
    
    if user:
        student_profile = analytics_service.get_student_profile(
            user.id, 
            lti_context.get('context_id')
        )
        context['student_level'] = student_profile.get('recommended_difficulty', 'medium')
        
        if student_profile.get('needs_intervention'):
            predictive_hint = llm_service.get_predictive_hint(
                topic,
                student_profile,
                user_message
            )
            if predictive_hint:
                context['predictive_hint'] = predictive_hint
    
    # Inject Adaptive Memory context
    if user:
        mem_context = memory_service.build_memory_context(user.id, lti_context.get('resource_id', 'default'))
        context.update(mem_context)

    # Inject RAG context (document knowledge base)
    try:
        from services import rag_service
        resource_id = lti_context.get('resource_id', 'default')
        rag_ctx = rag_service.retrieve_context(user_message, resource_id, k=3)
        if rag_ctx:
            context['rag_context'] = rag_ctx
    except Exception:
        pass  # RAG is optional

    llm_service = LLMFactory.get_tutor()
    ai_response = llm_service.get_response(
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

    # Update adaptive memory every 5 exchanges (best-effort, non-blocking)
    if tutor_session and user:
        msgs = Message.get_by_session(tutor_session.id)
        lti_ctx = session.get('lti_context', {})
        if len(msgs) % 10 == 0:   # every 5 back-and-forth exchanges
            resource_id = lti_ctx.get('resource_id', 'default')
            memory_service.update_memory_from_session(user.id, resource_id, tutor_session.id, llm_service)

    return jsonify(response_data)


@tutor_bp.route('/welcome', methods=['GET'])
def get_welcome():
    """Return a personalized welcome message based on user's adaptive memory"""
    lti_user_data = session.get('lti_user', {})
    lti_context = session.get('lti_context', {})
    user = get_current_user()

    user_name = lti_user_data.get('name', 'Estudiante')
    resource_id = lti_context.get('resource_id', 'default')

    if not user:
        return jsonify({
            'welcome': f"¡Hola, {user_name}! 👋 Bienvenido/a. Soy tu tutor virtual.",
            'has_history': False
        })

    llm_service = LLMFactory.get_tutor()
    welcome_msg = memory_service.generate_welcome_message(
        user_name=user_name,
        user_id=user.id,
        resource_id=resource_id,
        llm_service=llm_service
    )

    mem = __import__('models').AdaptiveMemory.get(user.id, resource_id)
    return jsonify({
        'welcome': welcome_msg,
        'has_history': mem is not None and mem.session_count > 0,
        'memory': mem.to_dict() if mem else None
    })


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
    
    analysis = llm_service.analyze_answer(
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
    
    hint = llm_service.get_predictive_hint(
        topic,
        student_profile,
        current_question
    )
    
    return jsonify({'hint': hint})
