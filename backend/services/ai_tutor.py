"""
AI Tutor Service - Handles AI-powered tutoring logic
"""
import os
from openai import OpenAI
from typing import List, Dict, Optional
import json


class AITutorService:
    """Service for AI-powered tutoring interactions"""
    
    def __init__(self):
        self.client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        
        self.system_prompt = """Eres un tutor virtual inteligente y empático especializado en educación. 
Tu objetivo es ayudar a los estudiantes a aprender de manera efectiva.

Características de tu comportamiento:
1. **Reactivo**: Respondes preguntas de manera clara y pedagógica
2. **Predictivo**: Anticipas dificultades basándote en el contexto del estudiante
3. **Socrático**: Guías al estudiante con preguntas cuando es apropiado
4. **Motivador**: Mantienes un tono positivo y alentador

Cuando detectes respuestas incorrectas:
- Explica por qué la respuesta es incorrecta sin ser condescendiente
- Proporciona pistas o pasos para llegar a la respuesta correcta
- Ofrece ejemplos adicionales si es necesario

Siempre responde en el mismo idioma que el estudiante usa."""

    def get_response(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        context: Dict = None
    ) -> str:
        """
        Generate an AI response based on user message and context
        """
        if not self.client:
            return self._get_fallback_response(user_message)
        
        messages = [{"role": "system", "content": self._build_system_prompt(context)}]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._get_fallback_response(user_message)
    
    def analyze_answer(
        self,
        question: str,
        student_answer: str,
        correct_answer: Optional[str] = None,
        context: Dict = None
    ) -> Dict:
        """
        Analyze a student's answer and provide feedback
        """
        if not self.client:
            return self._get_fallback_analysis(student_answer, correct_answer)
        
        analysis_prompt = f"""Analiza la siguiente respuesta del estudiante:

Pregunta: {question}
Respuesta del estudiante: {student_answer}
{"Respuesta correcta esperada: " + correct_answer if correct_answer else ""}

Proporciona un análisis JSON con el siguiente formato:
{{
    "is_correct": boolean,
    "score": float (0-100),
    "feedback": "explicación detallada para el estudiante",
    "hints": ["pista 1", "pista 2"] si la respuesta es incorrecta,
    "concepts_to_review": ["concepto 1", "concepto 2"] si aplica,
    "encouragement": "mensaje motivacional"
}}

Responde SOLO con el JSON, sin texto adicional."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un evaluador educativo experto. Responde solo en JSON válido."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            return self._get_fallback_analysis(student_answer, correct_answer)
        except Exception as e:
            print(f"Answer analysis error: {e}")
            return self._get_fallback_analysis(student_answer, correct_answer)
    
    def get_predictive_hint(
        self,
        topic: str,
        student_performance: Dict,
        current_question: str = None
    ) -> Optional[str]:
        """
        Generate predictive hints based on student's historical performance
        """
        if not self.client:
            return None
        
        avg_score = student_performance.get('average_score', 50)
        weak_areas = student_performance.get('weak_areas', [])
        
        if avg_score >= 80 and not weak_areas:
            return None  # Student is doing well, no intervention needed
        
        prompt = f"""Basándote en el perfil del estudiante:
- Tema actual: {topic}
- Puntuación promedio: {avg_score}%
- Áreas débiles: {', '.join(weak_areas) if weak_areas else 'No identificadas'}
{"- Pregunta actual: " + current_question if current_question else ""}

Genera una pista proactiva y útil que ayude al estudiante antes de que cometa un error común.
La pista debe ser breve (máximo 2 oraciones) y no revelar la respuesta directamente."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un tutor predictivo. Proporciona pistas útiles y concisas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Predictive hint error: {e}")
            return None
    
    def _build_system_prompt(self, context: Dict = None) -> str:
        """Build system prompt with optional context"""
        prompt = self.system_prompt
        
        if context:
            if context.get('topic'):
                prompt += f"\n\nTema actual: {context['topic']}"
            if context.get('student_level'):
                prompt += f"\nNivel del estudiante: {context['student_level']}"
            if context.get('course_info'):
                prompt += f"\nInformación del curso: {context['course_info']}"
        
        return prompt
    
    def _get_fallback_response(self, message: str) -> str:
        """Fallback response when AI is not available"""
        return """¡Hola! Soy tu tutor virtual. 
        
Actualmente el servicio de IA no está disponible, pero puedo ayudarte con información básica.
Por favor, asegúrate de que la configuración de OpenAI esté correcta.

Si tienes preguntas específicas, intenta reformularlas o contacta a tu instructor."""
    
    def _get_fallback_analysis(self, student_answer: str, correct_answer: str = None) -> Dict:
        """Fallback analysis when AI is not available"""
        is_correct = False
        if correct_answer:
            is_correct = student_answer.strip().lower() == correct_answer.strip().lower()
        
        return {
            "is_correct": is_correct,
            "score": 100 if is_correct else 0,
            "feedback": "Respuesta correcta. ¡Buen trabajo!" if is_correct else "Tu respuesta necesita revisión.",
            "hints": [] if is_correct else ["Revisa el material del curso"],
            "concepts_to_review": [],
            "encouragement": "¡Sigue adelante!" if is_correct else "No te desanimes, sigue practicando."
        }


# Singleton instance
ai_tutor = AITutorService()
