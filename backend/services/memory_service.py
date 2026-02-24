"""
Adaptive Memory Service
Builds proactive welcome messages and keeps compressed summaries of past sessions.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, List

from models import AdaptiveMemory, Message, TutorSession, QuizResponse

logger = logging.getLogger(__name__)


def build_memory_context(user_id: str, resource_id: str) -> Dict:
    """
    Return a dict with everything known about this user in this resource.
    Used to inject context into LLM prompts.
    """
    mem = AdaptiveMemory.get(user_id, resource_id)
    if not mem:
        return {}
    return {
        'memory_summary': mem.summary,
        'last_topics': mem.last_topics,
        'weak_areas': mem.weak_areas,
        'strong_areas': mem.strong_areas,
        'session_count': mem.session_count,
        'average_quiz_score': mem.average_quiz_score,
        'last_seen': mem.last_seen.isoformat() if mem.last_seen else None,
    }


def generate_welcome_message(user_name: str, user_id: str, resource_id: str, llm_service) -> str:
    """
    Generate a personalized welcome message based on the user's history.
    Falls back to a generic greeting for first-time visitors.
    """
    mem = AdaptiveMemory.get(user_id, resource_id)

    # First time — no history
    if not mem or mem.session_count == 0:
        return (f"¡Hola, {user_name}! 👋 Bienvenido/a. "
                "Soy tu tutor virtual. ¿En qué tema te puedo ayudar hoy?")

    # Build a rich personalized context
    days_ago = ""
    if mem.last_seen:
        from datetime import timezone
        delta = datetime.utcnow() - mem.last_seen.replace(tzinfo=None) if mem.last_seen.tzinfo else datetime.utcnow() - mem.last_seen
        days = delta.days
        if days == 0:
            days_ago = "hoy"
        elif days == 1:
            days_ago = "ayer"
        else:
            days_ago = f"hace {days} días"

    prompt_parts = [f"Genera un saludo corto y motivador (2-3 oraciones) para {user_name}."]
    if mem.session_count:
        prompt_parts.append(f"Ha tenido {mem.session_count} sesiones previas.")
    if mem.last_topics:
        prompt_parts.append(f"Últimos temas: {', '.join(mem.last_topics[:3])}.")
    if mem.weak_areas:
        prompt_parts.append(f"Áreas de dificultad: {', '.join(mem.weak_areas[:2])}. Sugiere practicarlas.")
    if mem.average_quiz_score is not None:
        prompt_parts.append(f"Promedio de quiz: {mem.average_quiz_score:.0f}%. Comenta brevemente.")
    if days_ago:
        prompt_parts.append(f"La última sesión fue {days_ago}.")
    prompt_parts.append("El saludo debe ser en español, cálido y motivador. No menciones que eres una IA.")

    try:
        message = llm_service.get_response(
            " ".join(prompt_parts),
            context={'user_name': user_name}
        )
        return message
    except Exception as e:
        logger.warning(f"Could not generate personalized welcome: {e}")
        topics_str = ', '.join(mem.last_topics[:2]) if mem.last_topics else 'nuestros temas'
        return (f"¡Bienvenido/a de nuevo, {user_name}! 🎉 "
                f"En tu último encuentro estuvimos explorando {topics_str}. "
                "¿Continuamos donde lo dejamos?")


def update_memory_from_session(user_id: str, resource_id: str, session_id: str, llm_service) -> None:
    """
    After a session ends (or after N messages), compress the session into the
    user's adaptive memory. Runs asynchronously / best-effort.
    """
    try:
        messages = Message.get_by_session(session_id)
        if not messages:
            return

        mem = AdaptiveMemory.get_or_create(user_id, resource_id)
        mem.session_count += 1
        mem.total_messages += len(messages)
        mem.last_seen = datetime.utcnow()

        # Extract topics from the conversation
        user_messages = [m.content for m in messages if m.role == 'user'][:10]
        if not user_messages:
            mem.save()
            return

        conversation_text = "\n".join(f"- {m}" for m in user_messages)

        compression_prompt = f"""Analiza esta conversación de un estudiante con su tutor:
{conversation_text}

Responde en JSON con:
{{
  "topics": ["tema1", "tema2"],       // max 3, temas principales
  "weak_areas": ["area1"],            // max 2, donde el estudiante tuvo dificultades (vacío si no aplica)
  "strong_areas": ["area1"],          // max 2, donde demostró dominio (vacío si no aplica)
  "summary": "Una frase resumiendo la sesión"
}}
Solo responde con JSON válido."""

        try:
            result_text = llm_service.get_response(compression_prompt, context={})
            import json
            text = result_text.strip()
            if text.startswith('```json'): text = text[7:]
            if text.startswith('```'): text = text[3:]
            if text.endswith('```'): text = text[:-3]
            data = json.loads(text.strip())

            new_topics = data.get('topics', [])
            # Merge: keep unique, most recent first
            mem.last_topics = list(dict.fromkeys(new_topics + mem.last_topics))[:5]

            new_weak = data.get('weak_areas', [])
            mem.weak_areas = list(dict.fromkeys(new_weak + mem.weak_areas))[:3]

            new_strong = data.get('strong_areas', [])
            mem.strong_areas = list(dict.fromkeys(new_strong + mem.strong_areas))[:3]

            mem.summary = data.get('summary', mem.summary)
        except Exception as e:
            logger.warning(f"Memory compression failed: {e}")

        mem.save()
        logger.info(f"Updated adaptive memory for user {user_id} in resource {resource_id}")

    except Exception as e:
        logger.error(f"update_memory_from_session error: {e}")


def update_quiz_score(user_id: str, resource_id: str, score: float) -> None:
    """Update the rolling average quiz score in memory."""
    try:
        mem = AdaptiveMemory.get_or_create(user_id, resource_id)
        if mem.average_quiz_score is None:
            mem.average_quiz_score = score
        else:
            # Exponential moving average (weight 0.3 for new score)
            mem.average_quiz_score = round(0.7 * mem.average_quiz_score + 0.3 * score, 1)
        mem.save()
    except Exception as e:
        logger.error(f"update_quiz_score error: {e}")
