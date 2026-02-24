import React, { useState, useEffect, useRef } from 'react'

const TUTOR_WELCOME = "¡Hola! 👋 Soy tu tutor virtual. Estoy aquí para guiarte durante el examen. Selecciona una respuesta y te daré retroalimentación inmediata. No te preocupes por equivocarte, ¡aprender de los errores es parte del proceso!"

export default function QuizView({ quizData, userName, tutorPrompt }) {
    const [currentQ, setCurrentQ] = useState(0)
    const [answers, setAnswers] = useState({})
    const [submitted, setSubmitted] = useState(false)
    const [score, setScore] = useState(0)
    const [correctCount, setCorrectCount] = useState(0)

    // Tutor state
    const [tutorMessages, setTutorMessages] = useState([
        { role: 'tutor', text: TUTOR_WELCOME }
    ])
    const [tutorInput, setTutorInput] = useState('')
    const [tutorLoading, setTutorLoading] = useState(false)
    const [lastFeedbackFor, setLastFeedbackFor] = useState(null) // {qId, answerIdx}
    const tutorEndRef = useRef(null)

    useEffect(() => {
        tutorEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [tutorMessages])

    // Adaptive Welcome Message and AGS Check
    const [adaptiveWelcome, setAdaptiveWelcome] = useState(TUTOR_WELCOME)
    const [isGradeable, setIsGradeable] = useState(false)
    const [gradeSyncing, setGradeSyncing] = useState(false)
    const [syncResult, setSyncResult] = useState(null)

    useEffect(() => {
        const fetchMetadata = async () => {
            try {
                // Fetch welcome message
                const welcomeRes = await fetch('/api/tutor/welcome', { credentials: 'include' })
                if (welcomeRes.ok) {
                    const data = await welcomeRes.json()
                    setAdaptiveWelcome(data.welcome)
                    setTutorMessages([{ role: 'tutor', text: data.welcome }])
                }

                // Check if AGS is available
                const agsRes = await fetch('/api/grades/check', { credentials: 'include' })
                if (agsRes.ok) {
                    const data = await agsRes.json()
                    setIsGradeable(data.is_gradeable)
                }
            } catch (err) {
                console.error("Error fetching tutor metadata:", err)
            }
        }
        fetchMetadata()
    }, [])

    // When question changes, greet the new question context
    useEffect(() => {
        if (!quizData || quizData.length === 0) return
        const q = quizData[currentQ]
        if (!answers[q.id]) {
            addTutorMessage(`📌 **Pregunta ${currentQ + 1}:** Lee cuidadosamente el enunciado. Si necesitas una pista antes de responder, pregúntame.`)
        }
    }, [currentQ])

    const addTutorMessage = (text, role = 'tutor') => {
        setTutorMessages(prev => [...prev, { role, text }])
    }

    const evaluateAnswer = async (q, answerIdx) => {
        // Don't re-evaluate if already gave feedback for this exact answer
        if (lastFeedbackFor?.qId === q.id && lastFeedbackFor?.answerIdx === answerIdx) return
        setLastFeedbackFor({ qId: q.id, answerIdx })

        const correctAnswers = Array.isArray(q.correct_answer) ? q.correct_answer : [q.correct_answer]
        const isMultiple = q.type === 'multiple'

        // For single choice, give immediate feedback
        if (!isMultiple) {
            const isCorrect = correctAnswers.includes(answerIdx)

            if (isCorrect) {
                const positives = [
                    "¡Correcto! ✅ Muy bien, esa es la respuesta acertada.",
                    "¡Excelente! ✅ Lo tienes claro.",
                    "¡Perfecto! ✅ Eso es exactamente correcto."
                ]
                addTutorMessage(positives[Math.floor(Math.random() * positives.length)])
                if (q.explanation) {
                    setTimeout(() => addTutorMessage(`💡 **¿Por qué?** ${q.explanation}`), 800)
                }
            } else {
                const incorrectFeedback = `❌ Esa no es la respuesta correcta. No te desanimes, repásala con calma.`
                addTutorMessage(incorrectFeedback)
                setTutorLoading(true)
                try {
                    const context = `El estudiante respondió incorrectamente la siguiente pregunta de opción múltiple:\n\nPregunta: "${q.question}"\nRespuesta elegida: "${q.options[answerIdx]}"\nRespuestas correctas: ${correctAnswers.map(i => `"${q.options[i]}"`).join(', ')}\n${q.explanation ? `Explicación: ${q.explanation}` : ''}\n\nDa una explicación breve y pedagógica de por qué su respuesta fue incorrecta y guía al estudiante hacia el concepto correcto. No des directamente la respuesta. Máximo 3 oraciones.`
                    const res = await fetch('/api/tutor/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({ message: context, topic: 'Feedback de examen' })
                    })
                    const data = await res.json()
                    if (data.response) addTutorMessage(`🤖 ${data.response}`)
                } catch {
                    if (q.explanation) addTutorMessage(`💡 ${q.explanation}`)
                }
                setTutorLoading(false)
            }
        }
    }

    const handleAnswer = async (qId, idx, isMultiple) => {
        let newAnswers
        if (isMultiple) {
            const curr = answers[qId] || []
            const newSel = curr.includes(idx) ? curr.filter(a => a !== idx) : [...curr, idx]
            newAnswers = { ...answers, [qId]: newSel }
        } else {
            newAnswers = { ...answers, [qId]: idx }
        }
        setAnswers(newAnswers)

        const q = quizData[currentQ]
        if (!isMultiple) {
            await evaluateAnswer(q, idx)
        }
    }

    const handleCheckMultiple = async () => {
        const q = quizData[currentQ]
        const ua = answers[q.id] || []
        if (ua.length === 0) return

        const correctAnswers = Array.isArray(q.correct_answer) ? q.correct_answer : [q.correct_answer]
        const sortedUA = [...ua].sort()
        const sortedCA = [...correctAnswers].sort()
        const isCorrect = JSON.stringify(sortedUA) === JSON.stringify(sortedCA)

        if (isCorrect) {
            addTutorMessage("¡Correcto! ✅ Seleccionaste todas las opciones correctas.")
            if (q.explanation) setTimeout(() => addTutorMessage(`💡 **¿Por qué?** ${q.explanation}`), 800)
        } else {
            addTutorMessage("❌ Tu selección no es del todo correcta. Revisa cuáles opciones marcaste.")
            setTutorLoading(true)
            try {
                const context = `El estudiante respondió incorrectamente esta pregunta de selección múltiple:\n\nPregunta: "${q.question}"\nOpciones seleccionadas: ${ua.map(i => `"${q.options[i]}"`).join(', ')}\nRespuestas correctas: ${correctAnswers.map(i => `"${q.options[i]}"`).join(', ')}\n${q.explanation ? `Explicación: ${q.explanation}` : ''}\n\nDa retroalimentación breve: qué sobró o faltó en su selección, sin dar directamente las respuestas. Máximo 3 oraciones.`
                const res = await fetch('/api/tutor/chat', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
                    body: JSON.stringify({ message: context, topic: 'Feedback de examen' })
                })
                const data = await res.json()
                if (data.response) addTutorMessage(`🤖 ${data.response}`)
            } catch {
                if (q.explanation) addTutorMessage(`💡 ${q.explanation}`)
            }
            setTutorLoading(false)
        }
    }

    const askTutor = async () => {
        if (!tutorInput.trim() || tutorLoading) return
        const question = tutorInput.trim()
        setTutorInput('')
        addTutorMessage(question, 'student')
        setTutorLoading(true)
        try {
            const q = quizData[currentQ]
            const context = `Contexto del examen — Pregunta actual: "${q.question}"\nOpciones: ${q.options.map((o, i) => `${i + 1}. ${o}`).join(', ')}\n\nPregunta del estudiante: ${question}\n\nResponde pedagógicamente. No des la respuesta correcta directamente, orienta con pistas.`
            const res = await fetch('/api/tutor/chat', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
                body: JSON.stringify({ message: context, topic: 'Guía de examen' })
            })
            const data = await res.json()
            if (data.response) addTutorMessage(`🤖 ${data.response}`)
        } catch { addTutorMessage('No pude conectarme. Intenta de nuevo.') }
        setTutorLoading(false)
    }

    const handleSubmit = async () => {
        let correct = 0
        quizData.forEach(q => {
            const ua = answers[q.id]
            const ca = Array.isArray(q.correct_answer) ? q.correct_answer : [q.correct_answer]
            if (q.type === 'multiple') {
                if (JSON.stringify((Array.isArray(ua) ? ua : []).slice().sort()) === JSON.stringify([...ca].sort())) correct++
            } else {
                if (ua === ca[0]) correct++
            }
        })
        const finalScore = Math.round((correct / quizData.length) * 100)
        setCorrectCount(correct)
        setScore(finalScore)
        setSubmitted(true)

        // Sync with LTI AGS if possible
        if (isGradeable) {
            setGradeSyncing(true)
            try {
                const res = await fetch('/api/grades/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        score: correct,
                        max_score: quizData.length,
                        comment: `Completado con éxito. Puntuación: ${finalScore}%`
                    })
                })
                const data = await res.json()
                setSyncResult(data)
            } catch (err) {
                console.error("Grade sync error:", err)
            } finally {
                setGradeSyncing(false)
            }
        }
    }

    /* ── EMPTY STATE ── */
    if (!quizData || quizData.length === 0) {
        return (
            <div className="quiz-empty-state">
                <div className="qes-icon">📝</div>
                <h2>No hay evaluación disponible</h2>
                <p>El instructor aún no ha configurado preguntas para este recurso.</p>
            </div>
        )
    }

    /* ── RESULTS VIEW ── */
    if (submitted) {
        const emoji = score >= 80 ? '🏆' : score >= 60 ? '👍' : '💪'
        const color = score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : '#ef4444'
        return (
            <div className="quiz-results">
                <div className="qr-card">
                    <div className="qr-emoji">{emoji}</div>
                    <h2 className="qr-title">Evaluación Completada</h2>
                    <div className="qr-score" style={{ color }}>
                        {score}%
                        <div className="qr-score-sub">{correctCount} de {quizData.length} correctas</div>
                    </div>
                    <div className="qr-bar-wrap">
                        <div className="qr-bar-fill" style={{ width: `${score}%`, background: color }} />
                    </div>
                    <p className="qr-msg">
                        {score >= 80 ? '¡Excelente! Dominas este tema.' : score >= 60 ? 'Buen intento. Repasa los temas en rojo.' : 'Sigue estudiando, puedes mejorar.'}
                    </p>

                    {/* Grade Sync Status */}
                    {isGradeable && (
                        <div className={`qr-sync-status ${syncResult?.sent ? 'success' : 'pending'}`}>
                            {gradeSyncing ? (
                                <><span className="inst-spinner" /> Sincronizando nota con Open edX...</>
                            ) : syncResult?.sent ? (
                                <>✅ Nota enviada exitosamente al libro de calificaciones</>
                            ) : (
                                <>⚠️ No se pudo sincronizar la nota automáticamente</>
                            )}
                        </div>
                    )}
                </div>

                <div className="qr-breakdown">
                    <h3>Detalle por pregunta</h3>
                    {quizData.map((q, i) => {
                        const ua = answers[q.id]
                        const ca = Array.isArray(q.correct_answer) ? q.correct_answer : [q.correct_answer]
                        let ok = q.type === 'multiple'
                            ? JSON.stringify((Array.isArray(ua) ? ua : []).slice().sort()) === JSON.stringify([...ca].sort())
                            : ua === ca[0]
                        return (
                            <div key={i} className={`qr-item ${ok ? 'ok' : 'fail'}`}>
                                <div className="qr-item-status">{ok ? '✅' : '❌'}</div>
                                <div className="qr-item-body">
                                    <div className="qr-item-q">{q.question}</div>
                                    {!ok && q.explanation && <div className="qr-item-exp">💡 {q.explanation}</div>}
                                    <div className="qr-item-opts">
                                        {q.options.map((opt, oi) => {
                                            const isCorrect = ca.includes(oi)
                                            const wasChosen = Array.isArray(ua) ? ua.includes(oi) : ua === oi
                                            return (
                                                <div key={oi} className={`qr-opt ${isCorrect ? 'correct' : wasChosen && !isCorrect ? 'wrong' : ''}`}>
                                                    {opt}
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        )
    }

    /* ── QUESTION VIEW ── */
    const q = quizData[currentQ]
    const isMultiple = q.type === 'multiple'
    const ua = answers[q.id]
    const selected = Array.isArray(ua) ? ua : (ua !== undefined ? [ua] : [])
    const allAnswered = quizData.every(qz => {
        const a = answers[qz.id]
        return a !== undefined && (!Array.isArray(a) || a.length > 0)
    })

    return (
        <div className="quiz-view">
            {/* LEFT: Questions */}
            <div className="quiz-main">
                {/* Progress */}
                <div className="quiz-progress">
                    <div className="quiz-progress-info">
                        <span>Pregunta {currentQ + 1} de {quizData.length}</span>
                        {isMultiple && <span className="quiz-multiple-hint">☑️ Selección múltiple</span>}
                    </div>
                    <div className="quiz-progress-bar">
                        {quizData.map((_, i) => (
                            <div
                                key={i}
                                className={`quiz-progress-seg ${i < currentQ ? 'done' : i === currentQ ? 'current' : ''} ${answers[quizData[i].id] !== undefined ? 'answered' : ''}`}
                                onClick={() => setCurrentQ(i)}
                            />
                        ))}
                    </div>
                </div>

                {/* Question Card */}
                <div className="quiz-question-card">
                    <div className="qqc-num">P{currentQ + 1}</div>
                    <div className="qqc-text">{q.question}</div>
                    {isMultiple && <div className="qqc-hint">Selecciona todas las respuestas correctas</div>}

                    <div className="qqc-options">
                        {q.options.map((opt, i) => {
                            const isSelected = selected.includes(i)
                            return (
                                <button
                                    key={i}
                                    className={`qqc-opt ${isSelected ? 'selected' : ''} ${isMultiple ? 'multi' : 'single'}`}
                                    onClick={() => handleAnswer(q.id, i, isMultiple)}
                                >
                                    <div className="qqc-opt-indicator">
                                        {isMultiple
                                            ? <span className={`qqc-checkbox ${isSelected ? 'checked' : ''}`}>{isSelected ? '✓' : ''}</span>
                                            : <span className={`qqc-radio ${isSelected ? 'checked' : ''}`} />
                                        }
                                    </div>
                                    <span className="qqc-opt-letter">{String.fromCharCode(65 + i)}</span>
                                    <span className="qqc-opt-text">{opt}</span>
                                </button>
                            )
                        })}
                    </div>

                    {/* Multiple: verify button */}
                    {isMultiple && selected.length > 0 && (
                        <button className="quiz-check-btn" onClick={handleCheckMultiple} disabled={tutorLoading}>
                            {tutorLoading ? '⏳ Evaluando...' : '🤖 Verificar selección con tutor'}
                        </button>
                    )}
                </div>

                {/* Navigation */}
                <div className="quiz-nav">
                    <button className="quiz-nav-btn prev" onClick={() => setCurrentQ(p => p - 1)} disabled={currentQ === 0}>
                        ← Anterior
                    </button>
                    <div className="quiz-nav-dots">
                        {quizData.map((qz, i) => (
                            <button
                                key={i}
                                className={`quiz-dot ${i === currentQ ? 'active' : ''} ${answers[quizData[i].id] !== undefined ? 'answered' : ''}`}
                                onClick={() => setCurrentQ(i)}
                            />
                        ))}
                    </div>
                    {currentQ === quizData.length - 1 ? (
                        <button className="quiz-nav-btn submit" onClick={handleSubmit} disabled={!allAnswered} title={!allAnswered ? 'Responde todas las preguntas' : ''}>
                            ✓ Enviar
                        </button>
                    ) : (
                        <button className="quiz-nav-btn next" onClick={() => setCurrentQ(p => p + 1)}>
                            Siguiente →
                        </button>
                    )}
                </div>
            </div>

            {/* RIGHT: Tutor – always visible and proactive */}
            <div className="quiz-tutor-panel active">
                <div className="qtp-header-static">
                    <div className="qtp-avatar">🤖</div>
                    <div>
                        <div className="qtp-title">Tutor Virtual</div>
                        <div className="qtp-sub">{tutorLoading ? 'Escribiendo...' : 'Activo y listo para guiarte'}</div>
                    </div>
                    {tutorLoading && <div className="qtp-typing"><span /><span /><span /></div>}
                </div>

                <div className="qtp-messages">
                    {tutorMessages.map((m, i) => (
                        <div key={i} className={`qtp-msg ${m.role}`}>
                            {m.role === 'tutor' && <div className="qtp-msg-avatar">🤖</div>}
                            <div className="qtp-msg-bubble">
                                {m.text.split('**').map((part, pi) =>
                                    pi % 2 === 1 ? <strong key={pi}>{part}</strong> : part
                                )}
                            </div>
                            {m.role === 'student' && <div className="qtp-msg-avatar student">👤</div>}
                        </div>
                    ))}
                    {tutorLoading && (
                        <div className="qtp-msg tutor">
                            <div className="qtp-msg-avatar">🤖</div>
                            <div className="qtp-msg-bubble loading">
                                <span /><span /><span />
                            </div>
                        </div>
                    )}
                    <div ref={tutorEndRef} />
                </div>

                <div className="qtp-input-area">
                    <div className="qtp-hint-label">¿Tienes dudas? Pregúntame (sin pedir la respuesta directa)</div>
                    <div className="qtp-input-row">
                        <input
                            className="qtp-input"
                            value={tutorInput}
                            onChange={e => setTutorInput(e.target.value)}
                            placeholder="Pide una pista o explicación..."
                            onKeyDown={e => e.key === 'Enter' && askTutor()}
                            disabled={tutorLoading}
                        />
                        <button className="qtp-send" onClick={askTutor} disabled={tutorLoading || !tutorInput.trim()}>
                            ➤
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
