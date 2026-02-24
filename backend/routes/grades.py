"""
Grade Submission Routes - LTI AGS grade sync
"""
from flask import Blueprint, request, jsonify, session
from services import ags_service
import services.memory_service as memory_service
from services.llm_factory import LLMFactory
from models import User

grades_bp = Blueprint('grades', __name__, url_prefix='/api/grades')


def get_current_user():
    lti_user = session.get('lti_user', {})
    if not lti_user:
        return None
    return User.get_by_id(lti_user.get('id'))


@grades_bp.route('/submit', methods=['POST'])
def submit_grade():
    """
    Submit a quiz score to Open edX Gradebook via LTI AGS.
    Auto-detects if the activity is gradeable based on the LTI session.
    """
    data = request.get_json() or {}
    score = data.get('score', 0)          # Points earned
    max_score = data.get('max_score', 10) # Max possible
    comment = data.get('comment', 'Calificación automática del Tutor LTI')

    lti_user_data = session.get('lti_user', {})
    lti_context = session.get('lti_context', {})
    user_lti_id = lti_user_data.get('lti_user_id') or lti_user_data.get('id', '')

    # Build session context for AGS
    lti_session = {
        'lti_ags': session.get('lti_ags', {}),
        'lti_token_url': session.get('lti_token_url', ''),
    }

    # Attempt grade submission
    result = ags_service.submit_grade(
        score=float(score),
        max_score=float(max_score),
        user_id_lti=user_lti_id,
        comment=comment,
        lti_session=lti_session,
    )

    # Update adaptive memory quiz score
    user = get_current_user()
    if user:
        resource_id = lti_context.get('resource_id', 'default')
        percentage = round((float(score) / float(max_score)) * 100, 1) if max_score > 0 else 0
        memory_service.update_quiz_score(user.id, resource_id, percentage)

    return jsonify({
        **result,
        'score': score,
        'max_score': max_score,
        'is_gradeable': result.get('sent', False)
    })


@grades_bp.route('/check', methods=['GET'])
def check_gradeable():
    """Check if the current LTI context supports grade submission"""
    lti_session = {
        'lti_ags': session.get('lti_ags', {}),
    }
    return jsonify({
        'is_gradeable': ags_service.is_gradeable(lti_session),
        'has_ags_config': bool(session.get('lti_ags'))
    })
