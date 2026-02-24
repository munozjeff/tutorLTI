import os
import logging
from typing import Union, Optional
from services.gemini_tutor import GeminiTutorService
from services.ollama_tutor import OllamaTutor

class LLMFactory:
    _instance = None
    
    @classmethod
    def get_tutor(cls) -> Union[GeminiTutorService, OllamaTutor]:
        """
        Get the configured LLM Tutor service instance.
        """
        if cls._instance:
            return cls._instance
            
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
        
        logger = logging.getLogger(__name__)
        logger.info(f"LLMFactory initializing with provider: {provider}")
        
        system_prompt = """Eres un tutor virtual amigable y paciente. 
        Tu objetivo es ayudar a los estudiantes a aprender guiándolos, no dándoles respuestas directas.
        Sé conciso, usa emojis ocasionalmente y mantén un tono alentador."""
        
        if provider == 'ollama':
            base_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
            model = os.getenv('OLLAMA_MODEL', 'gemma:2b')
            cls._instance = OllamaTutor(
                base_url=base_url,
                model_name=model,
                system_prompt=system_prompt
            )
        else:
            # Default to Gemini
            cls._instance = GeminiTutorService(system_prompt=system_prompt)
            
        return cls._instance

    @classmethod
    def reset_tutor(cls):
        """Reset the singleton instance (useful for testing or config changes)"""
        cls._instance = None
