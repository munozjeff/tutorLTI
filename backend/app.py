"""
Main Flask Application for the LTI AI Tutor
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables before importing any application components
load_dotenv()

from config import config
from routes import lti_bp, tutor_bp, config_bp
from routes.lti_info import lti_info_bp
from routes.analytics import analytics_bp
from routes.grades import grades_bp
from routes.documents import documents_bp


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure CORS - Allow frontend and Open edX instance
    # This allows both the frontend and Open edX to make requests to the backend
    allowed_origins = [
        app.config.get('FRONTEND_URL', 'http://localhost:3000'),
    ]
    
    # Add Open edX issuer if configured
    lti_issuer = app.config.get('LTI_ISSUER', '')
    if lti_issuer and lti_issuer not in allowed_origins:
        allowed_origins.append(lti_issuer)
    
    # For local development, also allow localhost variants
    if app.config.get('FLASK_ENV') == 'development':
        allowed_origins.extend([
            'http://localhost:8000',  # Common Open edX LMS port
            'http://localhost:18000', # Tutor dev LMS
            'http://127.0.0.1:8000',
            'http://127.0.0.1:18000',
            'http://localhost:8001',  # Open edX Studio
            'http://localhost:18010', # Tutor dev Studio
        ])
    
    CORS(app, 
         origins=allowed_origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Register blueprints
    app.register_blueprint(lti_bp)
    app.register_blueprint(tutor_bp)
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(lti_info_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(grades_bp)
    app.register_blueprint(documents_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'LTI AI Tutor',
            'version': '1.0.0'
        })
    
    # Root endpoint with API info
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'name': 'LTI AI Tutor API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'lti_config': '/lti/config.json',
                'lti_login': '/lti/login',
                'lti_launch': '/lti/launch',
                'lti_dev_launch': '/lti/dev-launch',
                'lti_session': '/lti/session',
                'tutor_chat': '/api/tutor/chat',
                'tutor_analyze': '/api/tutor/analyze-answer',
                'tutor_analytics': '/api/tutor/analytics'
            }
        })
    
    return app


# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
