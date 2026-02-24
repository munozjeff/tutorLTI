from flask import Blueprint, request, jsonify, session
from models import LTIResourceConfig
from services.llm_factory import LLMFactory
from functools import wraps

config_bp = Blueprint('config', __name__)

def instructor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session roles set during LTI launch
        # Allow access if is_instructor is True OR if lti_user_role contains instructor
        is_instructor = session.get('is_instructor', False)
        user_role = session.get('lti_user_role', '')
        if not is_instructor and 'instructor' not in str(user_role).lower():
            # In development/demo mode, log a warning but allow if no LTI session
            if not session.get('lti_user_id'):
                import logging
                logging.warning('No LTI session - allowing request in dev mode')
            else:
                return jsonify({'error': 'Unauthorized: Instructor access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@config_bp.route('/<resource_id>', methods=['GET'])
def get_config(resource_id):
    """Get configuration for a specific resource link"""
    # Allow students to read config (to know mode), but maybe filter data later if needed
    config = LTIResourceConfig.get_or_create(resource_id)
    return jsonify(config.to_dict())

@config_bp.route('/<resource_id>', methods=['POST'])
@instructor_required
def update_config(resource_id):
    """Update configuration (Instructor only)"""
    data = request.json
    config = LTIResourceConfig.get_or_create(resource_id)
    
    if 'mode' in data:
        config.mode = data['mode']
    if 'tutor_prompt' in data:
        config.tutor_prompt = data['tutor_prompt']
    if 'quiz_data' in data:
        config.quiz_data = data['quiz_data']
        
    config.save()
    return jsonify(config.to_dict())

@config_bp.route('/generate_quiz', methods=['POST'])
@instructor_required
def generate_quiz():
    """Generate quiz questions using AI"""
    data = request.json
    topic = data.get('topic')
    num_questions = data.get('num_questions', 5)
    difficulty = data.get('difficulty', 'medium')

    if not topic:
        return jsonify({'error': 'Topic is required'}), 400

    llm_service = LLMFactory.get_tutor()
    try:
        questions = llm_service.generate_quiz(topic, num_questions, difficulty)
        if not questions:
            return jsonify({'error': 'No questions generated. The AI may be unavailable.'}), 503
        return jsonify({'questions': questions})
    except Exception as e:
        err = str(e)
        if '429' in err or 'RESOURCE_EXHAUSTED' in err:
            return jsonify({
                'error': 'Cuota de la API de Gemini agotada. Por favor espera unos minutos y vuelve a intentarlo.',
                'code': 'QUOTA_EXCEEDED'
            }), 503
        return jsonify({'error': f'Error de IA: {err[:100]}'}), 500

@config_bp.route('/templates', methods=['GET'])
@instructor_required
def list_templates():
    """List all templates (optionally filtered by context)"""
    from models import ConfigTemplate
    context_id = request.args.get('context_id')
    templates = ConfigTemplate.get_all(context_id)
    return jsonify({'templates': [t.to_dict() for t in templates]})

@config_bp.route('/templates', methods=['POST'])
@instructor_required
def create_template():
    """Create a new template"""
    from models import ConfigTemplate
    data = request.json
    
    template = ConfigTemplate(
        name=data.get('name', 'Nueva Plantilla'),
        context_id=data.get('context_id'),
        mode=data.get('mode', 'tutor'),
        tutor_prompt=data.get('tutor_prompt'),
        quiz_data=data.get('quiz_data', [])
    )
    template.save()
    return jsonify(template.to_dict())

@config_bp.route('/templates/<template_id>', methods=['DELETE'])
@instructor_required
def delete_template(template_id):
    """Delete a template"""
    from models import ConfigTemplate
    success = ConfigTemplate.delete(template_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Template not found'}), 404

@config_bp.route('/templates/<template_id>/apply', methods=['POST'])
@instructor_required
def apply_template(template_id):
    """Apply a template to a resource"""
    from models import ConfigTemplate
    data = request.json
    resource_id = data.get('resource_id')
    
    if not resource_id:
        return jsonify({'error': 'resource_id required'}), 400
    
    template = ConfigTemplate.get_by_id(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    # Apply template to resource config
    config = LTIResourceConfig.get_or_create(resource_id)
    config.mode = template.mode
    config.tutor_prompt = template.tutor_prompt
    config.quiz_data = template.quiz_data
    config.save()
    
    return jsonify(config.to_dict())

