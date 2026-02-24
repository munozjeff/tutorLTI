"""
Routes package for the LTI Tutor
"""
from .lti import lti_bp
from .tutor import tutor_bp
from .config import config_bp

__all__ = ['lti_bp', 'tutor_bp']
