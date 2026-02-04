"""
Configuration module for the LTI Tutor Backend
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # LTI Configuration
    LTI_ISSUER = os.getenv('LTI_ISSUER', '')
    LTI_CLIENT_ID = os.getenv('LTI_CLIENT_ID', '')
    LTI_DEPLOYMENT_ID = os.getenv('LTI_DEPLOYMENT_ID', '1')
    LTI_JWKS_URL = os.getenv('LTI_JWKS_URL', '')
    LTI_AUTH_URL = os.getenv('LTI_AUTH_URL', '')
    LTI_TOKEN_URL = os.getenv('LTI_TOKEN_URL', '')
    LTI_TOOL_URL = os.getenv('LTI_TOOL_URL', 'http://localhost:5000')
    
    # Frontend URL
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
