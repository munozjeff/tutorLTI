const API_BASE = '/api/tutor';
const LTI_BASE = '/lti';
const LTI_INFO_BASE = '/api/lti_info';

export async function getLTISession() {
    try {
        const response = await fetch(`${LTI_BASE}/session`, { credentials: 'include' });
        return await response.json();
    } catch (error) {
        return { authenticated: false, user: null, context: null };
    }
}

export async function getLTIContext() {
    try {
        const response = await fetch(`${LTI_INFO_BASE}/full_context`, { credentials: 'include' });
        return await response.json();
    } catch (error) {
        return { user: {}, course: {}, resource: {}, session: { authenticated: false } };
    }
}


export async function sendMessage(message, sessionId = null, topic = 'General') {
    const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message, session_id: sessionId, topic })
    });
    if (!response.ok) throw new Error('Failed to send message');
    return await response.json();
}

export async function analyzeAnswer(question, studentAnswer, correctAnswer = null) {
    const response = await fetch(`${API_BASE}/analyze-answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ question, student_answer: studentAnswer, correct_answer: correctAnswer })
    });
    if (!response.ok) throw new Error('Failed to analyze');
    return await response.json();
}

export async function getAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics`, { credentials: 'include' });
        return await response.json();
    } catch (error) {
        return { profile: null, interventions: [], quiz_history: [] };
    }
}

export async function getPredictiveHint(topic, question = null) {
    try {
        const response = await fetch(`${API_BASE}/hint`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ topic, question })
        });
        return await response.json();
    } catch (error) {
        return { hint: null };
    }
}

export async function getWelcome() {
    try {
        const response = await fetch(`${API_BASE}/welcome`, { credentials: 'include' });
        return await response.json();
    } catch (error) {
        return { welcome: "¡Hola! 👋 Bienvenido a tu tutoría personalizada.", has_history: false };
    }
}


export async function getResourceConfig(resourceId) {
    const response = await fetch(`/api/config/${resourceId}`, {
        credentials: 'include'
    })
    return response.json()
}

export async function saveResourceConfig(resourceId, config) {
    const response = await fetch(`/api/config/${resourceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(config)
    })
    return response.json()
}

export async function getTemplates(contextId = null) {
    const url = contextId ? `/api/config/templates?context_id=${contextId}` : '/api/config/templates'
    const response = await fetch(url, { credentials: 'include' })
    return response.json()
}

export async function createTemplate(templateData) {
    const response = await fetch('/api/config/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(templateData)
    })
    return response.json()
}

export async function deleteTemplate(templateId) {
    const response = await fetch(`/api/config/templates/${templateId}`, {
        method: 'DELETE',
        credentials: 'include'
    })
    return response.json()
}

export async function applyTemplate(templateId, resourceId) {
    const response = await fetch(`/api/config/templates/${templateId}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ resource_id: resourceId })
    })
    return response.json()
}
