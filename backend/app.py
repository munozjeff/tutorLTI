"""
Main Flask Application for the LTI AI Tutor
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from config import config
from routes import lti_bp, tutor_bp

load_dotenv()


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure CORS
    CORS(app, 
         origins=[app.config.get('FRONTEND_URL', 'http://localhost:3000')],
         supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(lti_bp)
    app.register_blueprint(tutor_bp)
    
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
