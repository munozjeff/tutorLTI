const API_BASE = '/api/tutor';
const LTI_BASE = '/lti';

export async function getLTISession() {
    try {
        const response = await fetch(`${LTI_BASE}/session`, { credentials: 'include' });
        return await response.json();
    } catch (error) {
        return { authenticated: false, user: null, context: null };
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
