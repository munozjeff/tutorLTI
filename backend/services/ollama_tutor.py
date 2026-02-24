import requests
import json
import logging
import os
import re
from typing import Dict, List, Optional

class OllamaTutor:
    def __init__(self, base_url: str, model_name: str, system_prompt: str = ""):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.logger = logging.getLogger(__name__)

    def _generate(self, prompt: str, system: str = None, timeout: int = 120) -> str:
        """Call Ollama API"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system or self.system_prompt,
            "stream": False
        }
        
        try:
            self.logger.info(f"Calling Ollama model {self.model_name} at {url} (timeout={timeout}s)")
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            self.logger.error(f"Ollama generation error: {e}")
            return self._get_fallback_response()

    def get_response(self, message: str, conversation_history: List[Dict] = None, context: Dict = None) -> str:
        """Get response for chat"""
        # For now, Ollama simple generate doesn't handle history easily in this method, 
        # but we can append history to the prompt if needed.
        # But we must at least accept the argument to avoid TypeError.
        full_system = self._build_system_prompt(context)
        return self._generate(message, system=full_system)

    def analyze_answer(self, question: str, student_answer: str, context: Dict = None) -> Dict:
        """Analyze answer for correctness"""
        prompt = f"""
        Question: {question}
        Student Answer: {student_answer}
        
        Analyze if the answer is correct provided the context.
        Return JSON with:
        {{
            "is_correct": boolean,
            "feedback": "string explaining why",
            "score": int (0-100)
        }}
        Only return the JSON.
        """
        response = self._generate(prompt, timeout=180)  # Analysis can be slow
        extracted = self._extract_json(response)
        if extracted:
            return extracted
            
        self.logger.error("Could not extract valid JSON from analysis response")
        return {"is_correct": False, "feedback": "Error al analizar la respuesta (IA falló)", "score": 0}

    def generate_quiz(self, topic: str, num_questions: int = 5, difficulty: str = 'medium') -> List[Dict]:
        """Generate quiz questions"""
        prompt = f"""Genera un cuestionario interactivo de {num_questions} preguntas sobre "{topic}". Dificultad: {difficulty}.
        
        EJEMPLO DE FORMATO REQUERIDO:
        [
          {{
            "id": "1",
            "question": "¿Cuál es la capital de Italia?",
            "options": ["Milán", "Roma", "Nápoles", "Venecia"],
            "correct_answer": 1,
            "explanation": "Roma es la capital y ciudad más grande de Italia."
          }}
        ]
        
        INSTRUCCIONES:
        - Responde ÚNICAMENTE con la lista JSON.
        - No incluyas texto de bienvenida ni despedida.
        - Asegúrate de que el JSON sea válido y esté completo.
        """
        # Quizzes are very slow to generate locally, so we use a high timeout
        response = self._generate(prompt, timeout=300)
        extracted = self._extract_json(response)
        if isinstance(extracted, list):
            return extracted
            
        self.logger.error(f"Failed to extract JSON list from quiz response: {response[:200]}...")
        raise ValueError("La IA no pudo generar un formato de cuestionario válido. Inténtalo de nuevo.")

    def _extract_json(self, text: str) -> Optional[any]:
        """Helper to extract JSON from model output that might contain surroundings"""
        if not text:
            return None
            
        # Try to find JSON block in markdown
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            candidate = json_match.group(1)
        else:
            # Try to find anything between [ ] or { }
            # We look for the first '[' or '{' and the last ']' or '}'
            start_bracket = text.find('[')
            start_brace = text.find('{')
            
            if start_bracket == -1 and start_brace == -1:
                return None
                
            if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
                start = start_bracket
                end = text.rfind(']')
            else:
                start = start_brace
                end = text.rfind('}')
                
            if start == -1 or end == -1 or end <= start:
                return None
                
            candidate = text[start:end+1]
            
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Last ditch effort: try to strip common artifacts
            try:
                candidate = candidate.strip().rstrip('`').strip()
                return json.loads(candidate)
            except:
                return None

    def _build_system_prompt(self, context: Dict = None) -> str:
        prompt = self.system_prompt
        if context:
            prompt += "\n\n=== CONTEXT ==="
            for k, v in context.items():
                if v: prompt += f"\n{k}: {v}"
            prompt += "\n=== END CONTEXT ===\n"
        return prompt

    def get_predictive_hint(self, topic: str, student_performance: Dict, current_question: str = None) -> Optional[str]:
        """Generate predictive hints"""
        avg_score = student_performance.get('average_score', 50)
        weak_areas = student_performance.get('weak_areas', [])
        
        if avg_score >= 80 and not weak_areas:
            return None
            
        prompt = f"""Based on student profile:
        - Topic: {topic}
        - Avg Score: {avg_score}%
        - Weak Areas: {', '.join(weak_areas) if weak_areas else 'None'}
        {"- Current Question: " + current_question if current_question else ""}
        
        Generate a short proactive hint (max 2 sentences) to help the student avoid common mistakes.
        Do not give the answer directly.
        """
        try:
            return self._generate(prompt)
        except:
            return None

    def _get_fallback_response(self) -> str:
        """Fallback response when AI is not available"""
        return """¡Hola! Soy tu tutor virtual. 
        
Actualmente el servicio de IA local (Ollama) no está respondiendo o está tardando demasiado.
Por favor, asegúrate de que el contenedor de Ollama esté corriendo y tenga suficiente memoria asignada.

Si el problema persiste, contacta a tu instructor."""
