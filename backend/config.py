"""
Configuration module for the LTI Tutor Backend
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    
    # Gemini Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    
    # LLM Provider Config
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'gemini')  # 'gemini' or 'ollama'
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://ollama:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma:2b')
    
    # LTI Configuration
    LTI_ISSUER = os.getenv('LTI_ISSUER', '')
    LTI_CLIENT_ID = os.getenv('LTI_CLIENT_ID', '')
    LTI_DEPLOYMENT_ID = os.getenv('LTI_DEPLOYMENT_ID', '1')
    LTI_JWKS_URL = os.getenv('LTI_JWKS_URL', '')
    LTI_AUTH_URL = os.getenv('LTI_AUTH_URL', '')
    LTI_TOKEN_URL = os.getenv('LTI_TOKEN_URL', '')
    LTI_TOOL_URL = os.getenv('LTI_TOOL_URL', 'http://localhost:5000')
    
    # RSA Keys for signing
    LTI_PRIVATE_KEY_PATH = os.getenv('LTI_PRIVATE_KEY_PATH', 'keys/private.pem')
    LTI_PUBLIC_KEY_PATH = os.getenv('LTI_PUBLIC_KEY_PATH', 'keys/public.pem')
    
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
