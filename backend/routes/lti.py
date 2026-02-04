"""
LTI 1.3 Routes for Open edX integration
"""
import os
from flask import Blueprint, request, redirect, session, jsonify
from functools import wraps
import jwt
import uuid

from models import User

lti_bp = Blueprint('lti', __name__, url_prefix='/lti')


def get_lti_config():
    """Get LTI configuration from environment"""
    return {
        'issuer': os.getenv('LTI_ISSUER', ''),
        'client_id': os.getenv('LTI_CLIENT_ID', ''),
        'deployment_id': os.getenv('LTI_DEPLOYMENT_ID', '1'),
        'auth_url': os.getenv('LTI_AUTH_URL', ''),
        'token_url': os.getenv('LTI_TOKEN_URL', ''),
        'jwks_url': os.getenv('LTI_JWKS_URL', ''),
        'tool_url': os.getenv('LTI_TOOL_URL', 'http://localhost:5000'),
    }


def lti_required(f):
    """Decorator to require valid LTI session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'lti_user' not in session:
            return jsonify({'error': 'LTI session required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@lti_bp.route('/config.json', methods=['GET'])
def lti_config_json():
    """Returns LTI tool configuration for registration"""
    config = get_lti_config()
    tool_url = config['tool_url']
    
    return jsonify({
        "title": "AI Tutor Virtual",
        "description": "Tutor virtual inteligente con IA para Open edX",
        "oidc_initiation_url": f"{tool_url}/lti/login",
        "target_link_uri": f"{tool_url}/lti/launch",
        "scopes": [
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/score"
        ],
        "public_jwk_url": f"{tool_url}/lti/jwks"
    })


@lti_bp.route('/jwks', methods=['GET'])
def jwks():
    """JSON Web Key Set endpoint"""
    return jsonify({"keys": []})


@lti_bp.route('/login', methods=['GET', 'POST'])
def lti_login():
    """OIDC Login initiation endpoint"""
    login_hint = request.values.get('login_hint', '')
    lti_message_hint = request.values.get('lti_message_hint', '')
    client_id = request.values.get('client_id', '')
    
    config = get_lti_config()
    
    state = str(uuid.uuid4())
    nonce = str(uuid.uuid4())
    session['lti_state'] = state
    session['lti_nonce'] = nonce
    
    auth_params = {
        'scope': 'openid',
        'response_type': 'id_token',
        'response_mode': 'form_post',
        'prompt': 'none',
        'client_id': client_id or config['client_id'],
        'redirect_uri': f"{config['tool_url']}/lti/launch",
        'login_hint': login_hint,
        'state': state,
        'nonce': nonce,
    }
    
    if lti_message_hint:
        auth_params['lti_message_hint'] = lti_message_hint
    
    auth_url = config['auth_url']
    if auth_url:
        query_string = '&'.join(f"{k}={v}" for k, v in auth_params.items())
        return redirect(f"{auth_url}?{query_string}")
    
    return redirect(f"{config['tool_url']}/lti/dev-launch")


@lti_bp.route('/launch', methods=['POST'])
def lti_launch():
    """LTI Launch endpoint"""
    id_token = request.form.get('id_token', '')
    state = request.form.get('state', '')
    
    if state != session.get('lti_state'):
        return jsonify({'error': 'Invalid state'}), 400
    
    try:
        claims = jwt.decode(id_token, options={"verify_signature": False})
        
        lti_user_id = claims.get('sub', '')
        email = claims.get('email', '')
        name = claims.get('name', claims.get('given_name', 'Student'))
        
        context = claims.get('https://purl.imsglobal.org/spec/lti/claim/context', {})
        resource_link = claims.get('https://purl.imsglobal.org/spec/lti/claim/resource_link', {})
        roles = claims.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
        
        role = 'student'
        if any('Instructor' in r for r in roles):
            role = 'instructor'
        elif any('Administrator' in r for r in roles):
            role = 'admin'
        
        user = User.get_by_lti_id(lti_user_id)
        if not user:
            user = User(lti_user_id=lti_user_id, email=email, name=name, role=role)
            user.save()
        else:
            user.email = email
            user.name = name
            user.role = role
            user.save()
        
        session['lti_user'] = user.to_dict()
        session['lti_context'] = {
            'context_id': context.get('id', ''),
            'context_title': context.get('title', ''),
            'resource_id': resource_link.get('id', ''),
            'resource_title': resource_link.get('title', '')
        }
        
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return redirect(frontend_url)
        
    except jwt.DecodeError as e:
        return jsonify({'error': f'Invalid token: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Launch error: {str(e)}'}), 500


@lti_bp.route('/dev-launch', methods=['GET'])
def dev_launch():
    """Development launch endpoint - simulates LTI launch for testing"""
    test_user_id = 'dev-user-123'
    
    user = User.get_by_lti_id(test_user_id)
    if not user:
        user = User(
            lti_user_id=test_user_id,
            email='developer@test.com',
            name='Desarrollador Test',
            role='student'
        )
        user.save()
    
    session['lti_user'] = user.to_dict()
    session['lti_context'] = {
        'context_id': 'dev-course-001',
        'context_title': 'Curso de Desarrollo',
        'resource_id': 'dev-resource-001',
        'resource_title': 'Tutor Virtual'
    }
    
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    return redirect(frontend_url)


@lti_bp.route('/session', methods=['GET'])
def get_session():
    """Get current LTI session information"""
    if 'lti_user' not in session:
        return jsonify({
            'authenticated': False,
            'user': None,
            'context': None
        })
    
    return jsonify({
        'authenticated': True,
        'user': session.get('lti_user'),
        'context': session.get('lti_context')
    })


@lti_bp.route('/logout', methods=['POST'])
def logout():
    """Clear LTI session"""
    session.pop('lti_user', None)
    session.pop('lti_context', None)
    session.pop('lti_state', None)
    session.pop('lti_nonce', None)
    return jsonify({'success': True})
