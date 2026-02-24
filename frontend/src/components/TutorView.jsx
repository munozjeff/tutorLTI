import React, { useEffect, useRef } from 'react'
import { sendMessage } from '../api'

export default function TutorView({
    session,
    ltiContext,
    messages,
    setMessages,
    input,
    setInput,
    loading,
    setLoading,
    sessionId,
    setSessionId,
    welcomeMessage
}) {
    const messagesEndRef = useRef(null)

    // Extract user data
    const userName = ltiContext?.user?.name || session?.user?.name || 'Estudiante'
    const userInitial = userName.charAt(0).toUpperCase()

    const suggestions = [
        "¿Puedes explicarme este concepto?",
        "Necesito ayuda con un ejercicio",
        "¿Cuáles son los errores más comunes?",
        "Dame un ejemplo práctico"
    ]

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

    return (
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
                            {welcomeMessage || "Soy tu tutor virtual con IA. Estoy aquí para ayudarte a aprender, resolver dudas y guiarte en tu proceso de aprendizaje."}
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
    )
}
