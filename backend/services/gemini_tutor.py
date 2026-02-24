"""
AI Tutor Service using Google Gemini AI Studio
"""
import os
from google import genai
from typing import List, Dict, Optional
import json


class GeminiTutorService:
    """Service for AI-powered tutoring using Google Gemini"""
    
    def __init__(self):
        self.client = None
        api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        
        if api_key:
            self.client = genai.Client(api_key=api_key)
        
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
        
        # Build the full prompt with system context
        full_prompt = self._build_system_prompt(context)
        
        # Add conversation history
        if conversation_history:
            full_prompt += "\n\nHistorial de conversación:\n"
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = "Usuario" if msg.get('role') == 'user' else "Asistente"
                full_prompt += f"{role}: {msg.get('content', '')}\n"
        
        # Add current message
        full_prompt += f"\n\nUsuario: {user_message}\n\nAsistente:"
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
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
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=analysis_prompt
            )
            
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            result = json.loads(response_text.strip())
            return result
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}, response: {response.text if 'response' in locals() else 'N/A'}")
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
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Predictive hint error: {e}")
            return None
    
    def generate_quiz(self, topic: str, num_questions: int = 5, difficulty: str = 'medium') -> List[Dict]:
        """
        Generate a quiz based on a topic using Gemini
        """
        if not self.client:
            return []
            
        prompt = f"""Genera un examen de {num_questions} preguntas sobre el tema: "{topic}".
Dificultad: {difficulty}.

El formato debe ser JSON con la siguiente estructura exacta para cada pregunta:
[
  {{
    "id": "1",
    "question": "¿Pregunta?",
    "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
    "correct_answer": 0, (índice de la respuesta correcta, 0-3)
    "explanation": "Explicación breve de por qué es correcta"
  }}
]

Responde SOLO con el JSON válido, sin markdown ni texto adicional."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Clean response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"Quiz generation error: {e}")
            raise  # Re-raise so caller can handle quota/API errors properly

    def _build_system_prompt(self, context: Dict = None) -> str:
        """Build system prompt with optional context"""
        prompt = self.system_prompt
        
        if context:
            prompt += "\n\n=== CONTEXTO DEL ESTUDIANTE ==="
            if context.get('user_name'):
                prompt += f"\nNombre del estudiante: {context['user_name']}"
            if context.get('user_role'):
                prompt += f"\nRol: {context['user_role']}"
            if context.get('course_name'):
                prompt += f"\nCurso: {context['course_name']}"
            if context.get('topic'):
                prompt += f"\nTema actual: {context['topic']}"
            if context.get('student_level'):
                prompt += f"\nNivel del estudiante: {context['student_level']}"
            if context.get('course_info'):
                prompt += f"\nInformación del curso: {context['course_info']}"
            # Adaptive Memory context
            if context.get('memory_summary'):
                prompt += f"\n\n=== HISTORIAL DEL ESTUDIANTE ===\n{context['memory_summary']}"
            if context.get('last_topics'):
                prompt += f"\nÚltimos temas: {', '.join(context['last_topics'])}"
            if context.get('weak_areas'):
                prompt += f"\nÁreas de dificultad: {', '.join(context['weak_areas'])}"
            # RAG document context
            if context.get('rag_context'):
                prompt += f"\n\n=== MATERIAL DEL CURSO (usa esto para responder) ===\n{context['rag_context']}\n=== FIN DEL MATERIAL ==="
            prompt += "\n=== FIN DEL CONTEXTO ===\n"

        return prompt
    
    def _get_fallback_response(self, message: str) -> str:
        """Fallback response when AI is not available"""
        return """¡Hola! Soy tu tutor virtual. 
        
Actualmente el servicio de IA no está disponible, pero puedo ayudarte con información básica.
Por favor, asegúrate de que la configuración de Gemini API esté correcta.

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
gemini_tutor = GeminiTutorService()
