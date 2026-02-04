import { useState, useEffect, useRef } from 'react'
import { getLTISession, sendMessage, getAnalytics, analyzeAnswer } from './api'

export default function App() {
    const [session, setSession] = useState({ authenticated: false, user: null, context: null })
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [sessionId, setSessionId] = useState(null)
    const [analytics, setAnalytics] = useState(null)
    const [mode, setMode] = useState('chat')
    const messagesEndRef = useRef(null)

    useEffect(() => {
        getLTISession().then(setSession)
        getAnalytics().then(setAnalytics)
    }, [])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSend = async () => {
        if (!input.trim() || loading) return
        const userMessage = input.trim()
        setInput('')
        setMessages(prev => [...prev, { role: 'user', content: userMessage, time: new Date() }])
        setLoading(true)

        try {
            const response = await sendMessage(userMessage, sessionId)
            setSessionId(response.session_id)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.response,
                hint: response.predictive_hint,
                time: new Date()
            }])
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Lo siento, hubo un error. Por favor intenta de nuevo.',
                time: new Date()
            }])
        }
        setLoading(false)
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    const suggestions = [
        "¿Puedes explicarme este concepto?",
        "Necesito ayuda con un ejercicio",
        "¿Cuáles son los errores más comunes?",
        "Dame un ejemplo práctico"
    ]

    const userName = session.user?.name || 'Estudiante'
    const userInitial = userName.charAt(0).toUpperCase()
    const overallScore = analytics?.profile?.overall_performance || 75

    return (
        <div className="app">
            <header className="header">
                <div className="header-content">
                    <div className="logo">
                        <div className="logo-icon">🎓</div>
                        <span className="logo-text">TutorIA</span>
                    </div>
                    <div className="mode-switcher">
                        <button className={`mode-btn ${mode === 'chat' ? 'active' : ''}`} onClick={() => setMode('chat')}>
                            💬 Chat
                        </button>
                        <button className={`mode-btn ${mode === 'quiz' ? 'active' : ''}`} onClick={() => setMode('quiz')}>
                            📝 Quiz
                        </button>
                    </div>
                    <div className="user-info">
                        <div className="user-avatar">{userInitial}</div>
                        <span className="user-name">{userName}</span>
                    </div>
                </div>
            </header>

            <main className="main-content">
                <aside className="sidebar">
                    <div className="glass-card">
                        <h3 className="card-title"><span className="card-title-icon">📊</span> Tu Progreso</h3>
                        <div className="progress-ring-container">
                            <div className="progress-ring">
                                <svg width="120" height="120" viewBox="0 0 120 120">
                                    <defs>
                                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                            <stop offset="0%" stopColor="#7c3aed" />
                                            <stop offset="100%" stopColor="#14b8a6" />
                                        </linearGradient>
                                    </defs>
                                    <circle className="progress-ring-bg" cx="60" cy="60" r="52" />
                                    <circle className="progress-ring-fill" cx="60" cy="60" r="52"
                                        strokeDasharray={`${2 * Math.PI * 52}`}
                                        strokeDashoffset={`${2 * Math.PI * 52 * (1 - overallScore / 100)}`} />
                                </svg>
                                <div className="progress-ring-text">
                                    <div className="progress-value">{Math.round(overallScore)}%</div>
                                    <div className="progress-label">Rendimiento</div>
                                </div>
                            </div>
                        </div>
                        <div className="analytics-grid">
                            <div className="stat-card">
                                <div className="stat-value">{analytics?.profile?.topics_mastered || 0}</div>
                                <div className="stat-label">Dominados</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-value">{analytics?.profile?.total_topics_studied || 0}</div>
                                <div className="stat-label">Estudiados</div>
                            </div>
                        </div>
                    </div>

                    {analytics?.profile?.weak_areas?.length > 0 && (
                        <div className="glass-card">
                            <h3 className="card-title"><span className="card-title-icon">🎯</span> Áreas a Mejorar</h3>
                            <div className="topics-list">
                                {analytics.profile.weak_areas.slice(0, 4).map((topic, i) => (
                                    <div key={i} className="topic-item">
                                        <div className="topic-status needs-work"></div>
                                        <span className="topic-name">{topic}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </aside>

                <section className="chat-container">
                    <div className="chat-header">
                        <div className="chat-header-info">
                            <div className="chat-avatar">🤖</div>
                            <div>
                                <div className="chat-title">Tutor Virtual</div>
                                <div className="chat-status">
                                    <span className="status-dot"></span>
                                    Listo para ayudarte
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="messages-container">
                        {messages.length === 0 ? (
                            <div className="empty-state">
                                <div className="empty-state-icon">🚀</div>
                                <h2 className="empty-state-title">¡Hola, {userName}!</h2>
                                <p className="empty-state-description">
                                    Soy tu tutor virtual con IA. Estoy aquí para ayudarte a aprender,
                                    resolver dudas y guiarte en tu proceso de aprendizaje.
                                </p>
                                <div className="suggestion-chips">
                                    {suggestions.map((s, i) => (
                                        <button key={i} className="suggestion-chip" onClick={() => setInput(s)}>
                                            {s}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <>
                                {messages.map((msg, i) => (
                                    <div key={i} className={`message ${msg.role}`}>
                                        <div className="message-avatar">
                                            {msg.role === 'user' ? userInitial : '🤖'}
                                        </div>
                                        <div>
                                            <div className="message-content">{msg.content}</div>
                                            {msg.hint && (
                                                <div className="hint-card">
                                                    <span className="hint-icon">💡</span>
                                                    <div className="hint-content">
                                                        <div className="hint-title">Sugerencia proactiva</div>
                                                        <div className="hint-text">{msg.hint}</div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                                {loading && (
                                    <div className="message assistant">
                                        <div className="message-avatar">🤖</div>
                                        <div className="typing-indicator">
                                            <div className="typing-dots">
                                                <div className="typing-dot"></div>
                                                <div className="typing-dot"></div>
                                                <div className="typing-dot"></div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="chat-input-container">
                        <div className="chat-input-wrapper">
                            <textarea
                                className="chat-input"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Escribe tu pregunta..."
                                rows={1}
                            />
                            <button className="btn-icon" onClick={handleSend} disabled={loading || !input.trim()}>
                                ➤
                            </button>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    )
}
