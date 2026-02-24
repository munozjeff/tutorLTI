"""
Analytics Routes - Class-wide stats for the Instructor Dashboard
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from services.analytics import analytics_service

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


def instructor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        lti_user = session.get('lti_user', {})
        # In dev (no LTI session) allow access; in production check role
        if lti_user and lti_user.get('role') not in ('instructor', 'admin', None):
            return jsonify({'error': 'Instructor access required'}), 403
        return f(*args, **kwargs)
    return decorated


@analytics_bp.route('/class/<resource_id>', methods=['GET'])
@instructor_required
def class_analytics(resource_id):
    """Return aggregated analytics for the instructor view"""
    heatmap = analytics_service.get_class_heatmap(resource_id)
    engagement = analytics_service.get_engagement_stats(resource_id)
    mastery = analytics_service.get_topic_mastery(resource_id)
    interventions = analytics_service.get_students_needing_help(resource_id)

    return jsonify({
        'heatmap': heatmap,
        'engagement': engagement,
        'mastery': mastery,
        'students_needing_help': interventions,
    })
