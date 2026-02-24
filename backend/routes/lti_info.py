"""
LTI Context endpoint - Returns all available LTI data for personalization
"""
from flask import Blueprint, session, jsonify

lti_info_bp = Blueprint('lti_info', __name__, url_prefix='/api/lti_info')


@lti_info_bp.route('/full_context', methods=['GET'])
def get_full_context():
    """
    Returns ALL available LTI context data for the current session.
    This includes user, course, and resource information.
    """
    lti_user = session.get('lti_user', {})
    lti_context = session.get('lti_context', {})
    
    # Debug logging
    print(f"DEBUG lti_user: {lti_user}")
    print(f"DEBUG lti_context: {lti_context}")
    
    result = {
        'user': {
            'id': lti_user.get('id'),
            'lti_user_id': lti_user.get('lti_user_id'),
            'name': lti_user.get('name', 'Estudiante'),
            'email': lti_user.get('email', ''),
            'role': lti_user.get('role', 'student'),
            'is_instructor': lti_user.get('role') in ['instructor', 'admin'],
            'is_admin': lti_user.get('role') == 'admin'
        },
        'course': {
            'context_id': lti_context.get('context_id', ''),
            'context_title': lti_context.get('context_title', ''),
            'course_name': lti_context.get('context_title', 'Curso')
        },
        'resource': {
            'resource_id': lti_context.get('resource_id', ''),
            'resource_title': lti_context.get('resource_title', ''),
            'resource_name': lti_context.get('resource_title', 'Tutor Virtual')
        },
        'session': {
            'authenticated': bool(lti_user),
            'has_context': bool(lti_context)
        }
    }
    
    print(f"DEBUG result: {result}")
    
    return jsonify(result)
