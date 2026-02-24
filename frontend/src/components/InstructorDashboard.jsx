import React, { useState, useEffect } from 'react'
import { getTemplates, createTemplate, deleteTemplate, applyTemplate } from '../api'

export default function InstructorDashboard({ resourceId, currentConfig, onSaveConfig }) {
    const [activeTab, setActiveTab] = useState('mode')
    const [config, setConfig] = useState({ mode: 'tutor', tutor_prompt: '', quiz_data: [] })
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)

    // Quiz editor state
    const [quizTopic, setQuizTopic] = useState('')
    const [generatingQuiz, setGeneratingQuiz] = useState(false)
    const [editingQuestion, setEditingQuestion] = useState(null)

    // Templates state
    const [templates, setTemplates] = useState([])
    const [templateName, setTemplateName] = useState('')
    const [showSaveTemplate, setShowSaveTemplate] = useState(false)

    useEffect(() => {
        if (currentConfig) {
            setConfig({
                mode: currentConfig.mode || 'tutor',
                tutor_prompt: currentConfig.tutor_prompt || '',
                quiz_data: currentConfig.quiz_data || []
            })
        }
        loadTemplates()
    }, [currentConfig])

    const loadTemplates = async () => {
        try {
            const data = await getTemplates()
            setTemplates(data.templates || [])
        } catch { setTemplates([]) }
    }

    const handleSave = async () => {
        setSaving(true)
        await onSaveConfig(config)
        setSaving(false)
        setSaved(true)
        setTimeout(() => setSaved(false), 3000)
    }

    const handleSaveTemplate = async () => {
        if (!templateName.trim()) return
        await createTemplate({ name: templateName, ...config })
        setTemplateName('')
        setShowSaveTemplate(false)
        loadTemplates()
    }

    const handleApplyTemplate = async (templateId) => {
        const result = await applyTemplate(templateId, resourceId)
        setConfig({ mode: result.mode, tutor_prompt: result.tutor_prompt, quiz_data: result.quiz_data })
        setSaved(false)
    }

    const [genError, setGenError] = useState('')

    const generateQuiz = async () => {
        if (!quizTopic.trim()) return
        setGeneratingQuiz(true)
        setGenError('')
        try {
            const res = await fetch('/api/config/generate_quiz', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ topic: quizTopic })
            })
            const data = await res.json()
            if (!res.ok) {
                setGenError(data.error || 'Error al generar preguntas.')
            } else if (data.questions?.length) {
                setConfig(prev => ({ ...prev, quiz_data: [...prev.quiz_data, ...data.questions] }))
                setQuizTopic('')
            } else {
                setGenError('No se generaron preguntas. Intenta de nuevo.')
            }
        } catch (e) {
            setGenError('Error de conexión al generar el quiz.')
        }
        setGeneratingQuiz(false)
    }

    const addQuestion = () => setEditingQuestion({
        id: Date.now().toString(), question: '', type: 'single',
        options: ['', '', '', ''], correct_answer: [0], explanation: ''
    })

    const saveQuestion = () => {
        if (!editingQuestion.question.trim()) return
        const idx = config.quiz_data.findIndex(q => q.id === editingQuestion.id)
        const newQuizData = [...config.quiz_data]
        if (idx >= 0) newQuizData[idx] = editingQuestion
        else newQuizData.push(editingQuestion)
        setConfig({ ...config, quiz_data: newQuizData })
        setEditingQuestion(null)
    }

    const toggleCorrect = (i) => {
        const correct = editingQuestion.correct_answer || []
        if (editingQuestion.type === 'single') {
            setEditingQuestion({ ...editingQuestion, correct_answer: [i] })
        } else {
            const has = correct.includes(i)
            setEditingQuestion({ ...editingQuestion, correct_answer: has ? correct.filter(c => c !== i) : [...correct, i] })
        }
    }

    // Analytics state
    const [analyticsData, setAnalyticsData] = useState(null)
    const [loadingAnalytics, setLoadingAnalytics] = useState(false)

    // Documents state
    const [documents, setDocuments] = useState([])
    const [uploadingDoc, setUploadingDoc] = useState(false)
    const [docError, setDocError] = useState('')
    const [docSuccess, setDocSuccess] = useState('')

    const loadAnalytics = async () => {
        if (!resourceId) return
        setLoadingAnalytics(true)
        try {
            const res = await fetch(`/api/analytics/class/${resourceId}`, { credentials: 'include' })
            if (res.ok) setAnalyticsData(await res.json())
        } catch { } finally { setLoadingAnalytics(false) }
    }

    const loadDocuments = async () => {
        if (!resourceId) return
        try {
            const res = await fetch(`/api/documents/${resourceId}`, { credentials: 'include' })
            if (res.ok) {
                const data = await res.json()
                setDocuments(data.documents || [])
            }
        } catch { }
    }

    const handleDocUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return
        setUploadingDoc(true); setDocError(''); setDocSuccess('')
        const formData = new FormData()
        formData.append('file', file)
        formData.append('resource_id', resourceId || 'default')
        try {
            const res = await fetch('/api/documents/upload', {
                method: 'POST',
                credentials: 'include',
                body: formData
            })
            const data = await res.json()
            if (res.ok) { setDocSuccess(data.message); loadDocuments() }
            else setDocError(data.error || 'Error al subir')
        } catch { setDocError('Error de conexión') }
        setUploadingDoc(false)
    }

    const handleDeleteDoc = async (docId) => {
        if (!confirm('¿Eliminar documento del índice?')) return
        try {
            await fetch(`/api/documents/${resourceId || 'default'}/${docId}`, {
                method: 'DELETE', credentials: 'include'
            })
            loadDocuments()
        } catch { }
    }

    const tabs = [
        { id: 'mode', icon: '🎛️', label: 'Modo' },
        { id: 'tutor', icon: '🤖', label: 'Tutor IA' },
        { id: 'quiz', icon: '📋', label: 'Examen' },
        { id: 'docs', icon: '📚', label: 'Documentos' },
        { id: 'analytics', icon: '📊', label: 'Analíticas' },
        { id: 'templates', icon: '📂', label: 'Plantillas' }
    ]

    return (
        <div className="instructor-root">
            {/* Sidebar Navigation */}
            <nav className="inst-nav">
                <div className="inst-nav-header">
                    <div className="inst-nav-icon">👨‍🏫</div>
                    <div>
                        <div className="inst-nav-title">Panel Instructor</div>
                        <div className="inst-nav-sub">Configuración del recurso</div>
                    </div>
                </div>
                <div className="inst-nav-tabs">
                    {tabs.map(t => (
                        <button
                            key={t.id}
                            className={`inst-tab-btn ${activeTab === t.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(t.id)}
                        >
                            <span className="inst-tab-icon">{t.icon}</span>
                            <span>{t.label}</span>
                            {t.id === 'quiz' && config.quiz_data.length > 0 && (
                                <span className="inst-badge">{config.quiz_data.length}</span>
                            )}
                        </button>
                    ))}
                </div>

                {/* Current Mode Preview */}
                <div className="inst-mode-preview">
                    <div className="inst-mode-preview-label">Modo Activo</div>
                    <div className={`inst-mode-pill ${config.mode}`}>
                        {config.mode === 'tutor' ? '🤖 Tutor Virtual' : '📝 Examen'}
                    </div>
                </div>

                {/* Save Button */}
                <button className={`inst-save-btn ${saved ? 'saved' : ''}`} onClick={handleSave} disabled={saving}>
                    {saving ? (
                        <><span className="inst-spinner" />Guardando...</>
                    ) : saved ? (
                        <>✅ Guardado</>
                    ) : (
                        <>💾 Guardar Cambios</>
                    )}
                </button>
            </nav>

            {/* Main Panel */}
            <div className="inst-panel">

                {/* ── TAB: MODO ── */}
                {activeTab === 'mode' && (
                    <div className="inst-section">
                        <div className="inst-section-header">
                            <h2>🎛️ Selección de Modo</h2>
                            <p>Elige cómo verán este recurso los estudiantes</p>
                        </div>

                        <div className="mode-cards">
                            <button
                                className={`mode-card ${config.mode === 'tutor' ? 'selected' : ''}`}
                                onClick={() => setConfig({ ...config, mode: 'tutor' })}
                            >
                                <div className="mode-card-icon">🤖</div>
                                <div className="mode-card-title">Modo Tutor</div>
                                <div className="mode-card-desc">Los estudiantes pueden hacer consultas libremente al tutor virtual con IA</div>
                                <div className={`mode-card-badge ${config.mode === 'tutor' ? 'active' : ''}`}>
                                    {config.mode === 'tutor' ? '✓ Activo' : 'Seleccionar'}
                                </div>
                            </button>

                            <button
                                className={`mode-card ${config.mode === 'quiz' ? 'selected' : ''}`}
                                onClick={() => { setConfig({ ...config, mode: 'quiz' }); setActiveTab('quiz') }}
                            >
                                <div className="mode-card-icon">📝</div>
                                <div className="mode-card-title">Modo Examen</div>
                                <div className="mode-card-desc">Se presenta una evaluación con preguntas de selección. El tutor puede asistir</div>
                                <div className={`mode-card-badge ${config.mode === 'quiz' ? 'active' : ''}`}>
                                    {config.mode === 'quiz' ? '✓ Activo' : 'Seleccionar'}
                                </div>
                            </button>
                        </div>

                        {config.mode === 'quiz' && config.quiz_data.length === 0 && (
                            <div className="inst-alert warning">
                                ⚠️ Tienes el modo Examen activo pero no hay preguntas. Ve a la pestaña <strong>Examen</strong> para agregarlas.
                            </div>
                        )}
                        {config.mode === 'quiz' && config.quiz_data.length > 0 && (
                            <div className="inst-alert success">
                                ✅ Examen listo con <strong>{config.quiz_data.length} preguntas</strong>. Los estudiantes ya pueden tomarlo.
                            </div>
                        )}
                    </div>
                )}

                {/* ── TAB: TUTOR IA ── */}
                {activeTab === 'tutor' && (
                    <div className="inst-section">
                        <div className="inst-section-header">
                            <h2>🤖 Configuración del Tutor IA</h2>
                            <p>Define la personalidad y alcance del tutor virtual</p>
                        </div>

                        <div className="inst-field">
                            <label className="inst-label">Instrucciones del Tutor</label>
                            <p className="inst-field-hint">
                                Define el rol, personalidad y temas que puede responder el tutor. Cuanto más específico, mejor.
                            </p>
                            <textarea
                                className="inst-textarea"
                                rows={8}
                                value={config.tutor_prompt}
                                onChange={e => setConfig({ ...config, tutor_prompt: e.target.value })}
                                placeholder="Ejemplos:&#10;• Eres un experto en Cálculo Diferencial. Usa el método socrático.&#10;• Solo responde preguntas sobre Historia Universal del siglo XX.&#10;• Eres un tutor amigable de programación Python para principiantes."
                            />
                        </div>

                        <div className="inst-examples">
                            <div className="inst-examples-title">Ejemplos de prompts efectivos:</div>
                            {[
                                { icon: '🔢', title: 'Matemáticas', text: 'Eres un tutor de Álgebra Lineal. Guía al estudiante paso a paso sin dar la respuesta directa.' },
                                { icon: '🌎', title: 'Historia', text: 'Eres un historiador experto. Solo responde sobre la Segunda Guerra Mundial con fuentes verificables.' },
                                { icon: '💻', title: 'Programación', text: 'Eres un mentor de Python para principiantes. Usa analogías simples y ejemplos de código cortos.' }
                            ].map((ex, i) => (
                                <button key={i} className="inst-example-chip" onClick={() => setConfig({ ...config, tutor_prompt: ex.text })}>
                                    {ex.icon} {ex.title}
                                </button>
                            ))}
                        </div>
                        {config.tutor_prompt && (
                            <div className="inst-preview-box">
                                <div className="inst-preview-label">Vista previa de instrucciones:</div>
                                <div className="inst-preview-text">"{config.tutor_prompt}"</div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── TAB: EXAMEN ── */}
                {activeTab === 'quiz' && (
                    <div className="inst-section">
                        <div className="inst-section-header">
                            <h2>📋 Editor de Examen</h2>
                            <p>Crea preguntas manualmente o genera con IA</p>
                        </div>

                        {/* Question Editor */}
                        {editingQuestion ? (
                            <div className="question-editor">
                                <div className="qe-header">
                                    <h3>✏️ {config.quiz_data.find(q => q.id === editingQuestion.id) ? 'Editar' : 'Nueva'} Pregunta</h3>
                                    <button className="qe-close" onClick={() => setEditingQuestion(null)}>✕</button>
                                </div>

                                <div className="qe-field">
                                    <label className="inst-label">Tipo de pregunta</label>
                                    <div className="qe-type-selector">
                                        <button
                                            className={`qe-type-btn ${editingQuestion.type === 'single' ? 'active' : ''}`}
                                            onClick={() => setEditingQuestion({ ...editingQuestion, type: 'single', correct_answer: [0] })}
                                        >
                                            ⭕ Respuesta única
                                        </button>
                                        <button
                                            className={`qe-type-btn ${editingQuestion.type === 'multiple' ? 'active' : ''}`}
                                            onClick={() => setEditingQuestion({ ...editingQuestion, type: 'multiple', correct_answer: [] })}
                                        >
                                            ☑️ Respuesta múltiple
                                        </button>
                                    </div>
                                </div>

                                <div className="qe-field">
                                    <label className="inst-label">Enunciado de la pregunta</label>
                                    <textarea
                                        className="inst-textarea"
                                        rows={3}
                                        value={editingQuestion.question}
                                        onChange={e => setEditingQuestion({ ...editingQuestion, question: e.target.value })}
                                        placeholder="¿Cuál de las siguientes...?"
                                    />
                                </div>

                                <div className="qe-field">
                                    <label className="inst-label">
                                        Opciones — <span style={{ color: 'var(--accent-400)', fontSize: '13px' }}>
                                            {editingQuestion.type === 'single' ? 'Marca ⭕ la respuesta correcta' : 'Marca ☑️ todas las correctas'}
                                        </span>
                                    </label>
                                    <div className="qe-options">
                                        {editingQuestion.options.map((opt, i) => {
                                            const isCorrect = (editingQuestion.correct_answer || []).includes(i)
                                            return (
                                                <div key={i} className={`qe-option ${isCorrect ? 'correct' : ''}`}>
                                                    <button
                                                        className={`qe-correct-btn ${editingQuestion.type} ${isCorrect ? 'active' : ''}`}
                                                        onClick={() => toggleCorrect(i)}
                                                        title="Marcar como correcta"
                                                    >
                                                        {editingQuestion.type === 'single'
                                                            ? (isCorrect ? '⭕' : '○')
                                                            : (isCorrect ? '☑️' : '☐')
                                                        }
                                                    </button>
                                                    <input
                                                        className="qe-opt-input"
                                                        value={opt}
                                                        onChange={e => {
                                                            const opts = [...editingQuestion.options]
                                                            opts[i] = e.target.value
                                                            setEditingQuestion({ ...editingQuestion, options: opts })
                                                        }}
                                                        placeholder={`Opción ${String.fromCharCode(65 + i)}`}
                                                    />
                                                </div>
                                            )
                                        })}
                                    </div>
                                    {editingQuestion.options.length < 6 && (
                                        <button className="qe-add-opt" onClick={() => setEditingQuestion({ ...editingQuestion, options: [...editingQuestion.options, ''] })}>
                                            + Agregar opción
                                        </button>
                                    )}
                                </div>

                                <div className="qe-field">
                                    <label className="inst-label">Explicación (mostrada si falla)</label>
                                    <input
                                        className="qe-opt-input"
                                        value={editingQuestion.explanation}
                                        onChange={e => setEditingQuestion({ ...editingQuestion, explanation: e.target.value })}
                                        placeholder="Explica por qué la respuesta es correcta..."
                                    />
                                </div>

                                <div className="qe-actions">
                                    <button className="inst-btn primary" onClick={saveQuestion}>💾 Guardar Pregunta</button>
                                    <button className="inst-btn secondary" onClick={() => setEditingQuestion(null)}>Cancelar</button>
                                </div>
                            </div>
                        ) : (
                            <>
                                {/* AI Generator */}
                                <div className="ai-generator-box">
                                    <div className="ai-gen-title">
                                        <span>✨</span>
                                        <span>Generar preguntas con Gemini IA</span>
                                    </div>
                                    <div className="ai-gen-row">
                                        <input
                                            className="ai-gen-input"
                                            value={quizTopic}
                                            onChange={e => setQuizTopic(e.target.value)}
                                            placeholder="Tema: ej. Revolución Francesa, Álgebra Lineal..."
                                            onKeyDown={e => e.key === 'Enter' && generateQuiz()}
                                        />
                                        <button className="inst-btn primary" onClick={generateQuiz} disabled={generatingQuiz || !quizTopic.trim()}>
                                            {generatingQuiz ? <><span className="inst-spinner" />Generando...</> : '✨ Generar'}
                                        </button>
                                    </div>
                                    {genError && (
                                        <div className="inst-alert warning" style={{ marginTop: '10px' }}>
                                            ⚠️ {genError}
                                        </div>
                                    )}
                                </div>

                                {/* Add manual */}
                                <div className="quiz-toolbar">
                                    <span className="quiz-count">
                                        {config.quiz_data.length === 0 ? 'Sin preguntas' : `${config.quiz_data.length} pregunta${config.quiz_data.length > 1 ? 's' : ''}`}
                                    </span>
                                    <button className="inst-btn secondary" onClick={addQuestion}>
                                        ＋ Pregunta manual
                                    </button>
                                </div>

                                {/* Question list */}
                                {config.quiz_data.length === 0 ? (
                                    <div className="quiz-empty">
                                        <div style={{ fontSize: '48px', marginBottom: '12px' }}>📋</div>
                                        <p>No hay preguntas. Genera con IA o agrega manualmente.</p>
                                    </div>
                                ) : (
                                    <div className="quiz-list">
                                        {config.quiz_data.map((q, i) => {
                                            const corrects = Array.isArray(q.correct_answer) ? q.correct_answer : [q.correct_answer]
                                            return (
                                                <div key={q.id || i} className="quiz-item">
                                                    <div className="quiz-item-num">
                                                        <span>{i + 1}</span>
                                                    </div>
                                                    <div className="quiz-item-body">
                                                        <div className="quiz-item-header">
                                                            <span className={`quiz-item-type ${q.type || 'single'}`}>
                                                                {q.type === 'multiple' ? '☑️ Múltiple' : '⭕ Única'}
                                                            </span>
                                                            <div className="quiz-item-actions">
                                                                <button onClick={() => setEditingQuestion({ ...q, correct_answer: Array.isArray(q.correct_answer) ? q.correct_answer : [q.correct_answer], type: q.type || 'single' })}>✏️</button>
                                                                <button onClick={() => {
                                                                    const nd = [...config.quiz_data]
                                                                    nd.splice(i, 1)
                                                                    setConfig({ ...config, quiz_data: nd })
                                                                }}>🗑️</button>
                                                            </div>
                                                        </div>
                                                        <div className="quiz-item-question">{q.question}</div>
                                                        <div className="quiz-item-opts">
                                                            {q.options.map((opt, oi) => (
                                                                <div key={oi} className={`quiz-item-opt ${corrects.includes(oi) ? 'correct' : ''}`}>
                                                                    {corrects.includes(oi) ? '✅' : '○'} {opt}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}

                {/* ── TAB: PLANTILLAS ── */}
                {activeTab === 'templates' && (
                    <div className="inst-section">
                        <div className="inst-section-header">
                            <h2>📂 Plantillas Reutilizables</h2>
                            <p>Guarda y aplica configuraciones en múltiples bloques LTI</p>
                        </div>

                        {showSaveTemplate ? (
                            <div className="template-save-box">
                                <h3>Guardar configuración actual como plantilla</h3>
                                <input
                                    className="qe-opt-input"
                                    value={templateName}
                                    onChange={e => setTemplateName(e.target.value)}
                                    placeholder="Nombre de la plantilla (ej: Examen Unidad 1)"
                                />
                                <div className="qe-actions">
                                    <button className="inst-btn primary" onClick={handleSaveTemplate} disabled={!templateName.trim()}>
                                        💾 Guardar
                                    </button>
                                    <button className="inst-btn secondary" onClick={() => setShowSaveTemplate(false)}>Cancelar</button>
                                </div>
                            </div>
                        ) : (
                            <button className="inst-btn primary" onClick={() => setShowSaveTemplate(true)}>
                                💾 Guardar configuración actual como plantilla
                            </button>
                        )}

                        <div className="templates-list">
                            {templates.length === 0 ? (
                                <div className="quiz-empty">
                                    <div style={{ fontSize: '48px', marginBottom: '12px' }}>📂</div>
                                    <p>No hay plantillas. Guarda una configuración para reutilizarla.</p>
                                </div>
                            ) : (
                                templates.map(t => (
                                    <div key={t.id} className="template-card">
                                        <div className="template-card-icon">
                                            {t.mode === 'tutor' ? '🤖' : '📝'}
                                        </div>
                                        <div className="template-card-info">
                                            <div className="template-card-name">{t.name}</div>
                                            <div className="template-card-meta">
                                                Modo: {t.mode === 'tutor' ? 'Tutor' : 'Examen'} · {t.quiz_data?.length || 0} preguntas
                                            </div>
                                        </div>
                                        <div className="template-card-actions">
                                            <button className="inst-btn secondary small" onClick={() => handleApplyTemplate(t.id)}>
                                                📥 Aplicar
                                            </button>
                                            <button className="tpl-del-btn" onClick={async () => {
                                                await deleteTemplate(t.id)
                                                loadTemplates()
                                            }}>🗑️</button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* ========== DOCUMENTS TAB ========== */}
            {activeTab === 'docs' && (
                <div className="inst-panel">
                    <div className="inst-panel-title">📚 Base de Conocimiento</div>
                    <p style={{ color: 'var(--gray-400)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-4)' }}>
                        Sube documentos del curso (PDF, TXT, DOCX). El tutor los usará para responder con información precisa del material.
                    </p>

                    {/* Upload area */}
                    <label className="doc-upload-zone" style={{ display: "block", border: "2px dashed var(--glass-border)", borderRadius: "var(--radius-lg)", padding: "var(--space-8)", textAlign: "center", cursor: "pointer", marginBottom: "var(--space-4)", transition: "border-color 0.2s" }}
                        onMouseEnter={e => e.currentTarget.style.borderColor = "var(--primary-400)"}
                        onMouseLeave={e => e.currentTarget.style.borderColor = "var(--glass-border)"}>
                        <input type="file" accept=".pdf,.txt,.docx,.doc,.md" style={{ display: "none" }} onChange={handleDocUpload} disabled={uploadingDoc} />
                        <div style={{ fontSize: "48px", marginBottom: "var(--space-2)" }}>📄</div>
                        {uploadingDoc
                            ? <><div className="inst-spinner" style={{ display: "inline-block", marginRight: "8px" }} />Indexando documento...</>
                            : <>
                                <div style={{ fontWeight: 600, color: "var(--gray-200)" }}>Haz clic para subir un documento</div>
                                <div style={{ color: "var(--gray-400)", fontSize: "var(--font-size-sm)" }}>PDF, TXT, DOCX, Markdown — máx. 20MB</div>
                            </>
                        }
                    </label>

                        {/* Document list */}
                        <div style={{ marginTop: 'var(--space-4)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                                <span style={{ fontWeight: 600, color: 'var(--gray-200)' }}>Documentos indexados ({documents.length})</span>
                                <button className="inst-btn secondary" style={{ padding: '4px 12px', fontSize: '12px' }} onClick={loadDocuments}>↻ Refrescar</button>
                            </div>
                            {documents.length === 0
                                ? <div className="quiz-empty"><div style={{ fontSize: '32px' }}>📂</div><p>Sin documentos. Sube uno para que el tutor lo use.</p></div>
                                : documents.map(doc => (
                                    <div key={doc.doc_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--space-3)', background: 'var(--glass-bg)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-2)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                                            <span style={{ fontSize: '24px' }}>📄</span>
                                            <span style={{ color: 'var(--gray-200)' }}>{doc.filename}</span>
                                        </div>
                                        <button className="tpl-del-btn" onClick={() => handleDeleteDoc(doc.doc_id)}>🗑️</button>
                                    </div>
                                ))
                            }
                        </div>
                </div>
            )}

            {/* ========== ANALYTICS TAB ========== */}
            {activeTab === 'analytics' && (
                <div className="inst-panel">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                        <div className="inst-panel-title" style={{ margin: 0 }}>📊 Analíticas de la Clase</div>
                        <button className="inst-btn secondary" style={{ padding: '6px 14px', fontSize: '12px' }} onClick={loadAnalytics}>
                            {loadingAnalytics ? <><span className="inst-spinner" />Cargando...</> : '↻ Actualizar'}
                        </button>
                    </div>

                    {!analyticsData && !loadingAnalytics && (
                        <div className="quiz-empty">
                            <div style={{ fontSize: '48px' }}>📊</div>
                            <p>Haz clic en <b>Actualizar</b> para cargar las estadísticas del grupo.</p>
                        </div>
                    )}

                    {analyticsData && (<>
                        {/* Engagement Cards */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(120px,1fr))', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
                            {[
                                { label: 'Sesiones', value: analyticsData.engagement?.total_sessions ?? '—', icon: '💬' },
                                { label: 'Estudiantes', value: analyticsData.engagement?.unique_students ?? '—', icon: '👥' },
                                { label: 'Mensajes', value: analyticsData.engagement?.total_messages ?? '—', icon: '📨' },
                                { label: 'Promedio clase', value: analyticsData.mastery?.class_average ? `${analyticsData.mastery.class_average}%` : '—', icon: '📈' }
                            ].map(card => (
                                <div key={card.label} style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-4)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '28px', marginBottom: '4px' }}>{card.icon}</div>
                                    <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--primary-300)' }}>{card.value}</div>
                                    <div style={{ fontSize: '12px', color: 'var(--gray-400)' }}>{card.label}</div>
                                </div>
                            ))}
                        </div>

                        {/* Heatmap */}
                        {analyticsData.heatmap?.length > 0 && (
                            <div style={{ marginBottom: 'var(--space-6)' }}>
                                <div style={{ fontWeight: 600, color: 'var(--gray-200)', marginBottom: 'var(--space-3)' }}>🔥 Preguntas con mayor error</div>
                                {analyticsData.heatmap.slice(0, 8).map((q, i) => (
                                    <div key={i} style={{ marginBottom: 'var(--space-2)' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: 'var(--font-size-sm)' }}>
                                            <span style={{ color: 'var(--gray-300)', flex: 1, marginRight: '8px', overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{q.question_text}</span>
                                            <span style={{ color: q.error_rate > 60 ? 'var(--rose-400)' : q.error_rate > 30 ? '#f59e0b' : 'var(--success)', fontWeight: 600, flexShrink: 0 }}>{q.error_rate}% error</span>
                                        </div>
                                        <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                                            <div style={{ height: '100%', width: `${q.error_rate}%`, borderRadius: '4px', background: q.error_rate > 60 ? 'var(--rose-500)' : q.error_rate > 30 ? '#f59e0b' : 'var(--success)', transition: 'width 0.5s ease' }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Students needing help */}
                        {analyticsData.students_needing_help?.length > 0 && (
                            <div>
                                <div style={{ fontWeight: 600, color: 'var(--gray-200)', marginBottom: 'var(--space-3)' }}>🚨 Estudiantes que necesitan ayuda</div>
                                {analyticsData.students_needing_help.slice(0, 5).map((s, i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--space-3)', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-2)' }}>
                                        <div>
                                            <div style={{ fontWeight: 600, color: 'var(--gray-200)' }}>{s.name}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--gray-400)' }}>{s.topic} — {s.reason}</div>
                                        </div>
                                        <span style={{ fontWeight: 700, color: 'var(--rose-400)' }}>{s.score}%</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {analyticsData.heatmap?.length === 0 && analyticsData.students_needing_help?.length === 0 && (
                            <div className="quiz-empty"><div style={{ fontSize: '40px' }}>✨</div><p>No hay datos aún. Los datos aparecerán cuando los estudiantes completen actividades.</p></div>
                        )}
                    </>)}
                </div>
            )}

        </div>
        </div >
    )
}
