import { useState, useEffect } from 'react'
import { getLTISession, getLTIContext, getAnalytics, getResourceConfig, saveResourceConfig, getWelcome } from './api'
import TutorView from './components/TutorView'
import QuizView from './components/QuizView'
import InstructorDashboard from './components/InstructorDashboard'

export default function App() {
    const [session, setSession] = useState({ authenticated: false, user: null, context: null })
    const [ltiContext, setLtiContext] = useState({ user: {}, course: {}, resource: {}, session: {} })
    const [resourceConfig, setResourceConfig] = useState(null)
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [sessionId, setSessionId] = useState(null)
    const [analytics, setAnalytics] = useState(null)
    const [configLoading, setConfigLoading] = useState(true)
    const [personalWelcome, setPersonalWelcome] = useState(null)

    useEffect(() => {
        getLTISession().then(setSession)
        getLTIContext().then(data => {
            console.log('LTI Context received:', data)
            setLtiContext(data)

            // Fetch resource config
            const resourceId = data?.resource?.resource_id || 'default'
            getResourceConfig(resourceId)
                .then(config => {
                    setResourceConfig(config)
                    setConfigLoading(false)
                })
                .catch(err => {
                    console.error('Failed to load config:', err)
                    setConfigLoading(false)
                })
        })
        getAnalytics().then(setAnalytics)
        getWelcome().then(data => setPersonalWelcome(data.welcome))
    }, [])

    const handleSaveConfig = async (newConfig) => {
        const resourceId = ltiContext?.resource?.resource_id || 'default'
        const saved = await saveResourceConfig(resourceId, newConfig)
        setResourceConfig(saved)
    }

    // Extract user data with fallbacks
    const userName = ltiContext?.user?.name || session?.user?.name || 'Estudiante'
    const userInitial = userName.charAt(0).toUpperCase()
    const userRole = ltiContext?.user?.role || 'student'
    const isInstructor = ltiContext?.user?.is_instructor || false
    const courseName = ltiContext?.course?.course_name || ltiContext?.course?.context_title || ''
    const overallScore = analytics?.profile?.overall_performance || 75
    const resourceId = ltiContext?.resource?.resource_id || ''

    // Debug logging
    console.log('Display values:', { userName, userRole, isInstructor, courseName, resourceConfig })

    // Decide which view to show
    let mainContent
    if (configLoading) {
        mainContent = (
            <div className="chat-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="typing-indicator">
                    <div className="typing-dots">
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                    </div>
                </div>
            </div>
        )
    } else if (isInstructor) {
        // Instructors see the dashboard
        mainContent = (
            <InstructorDashboard
                resourceId={resourceId}
                currentConfig={resourceConfig}
                onSaveConfig={handleSaveConfig}
            />
        )
    } else {
        // Students see either Tutor or Quiz based on config
        const mode = resourceConfig?.mode || 'tutor'
        if (mode === 'quiz') {
            mainContent = (
                <QuizView
                    quizData={resourceConfig?.quiz_data || []}
                    userName={userName}
                />
            )
        } else {
            mainContent = (
                <TutorView
                    session={session}
                    ltiContext={ltiContext}
                    messages={messages}
                    setMessages={setMessages}
                    input={input}
                    setInput={setInput}
                    loading={loading}
                    setLoading={setLoading}
                    sessionId={sessionId}
                    setSessionId={setSessionId}
                    welcomeMessage={personalWelcome}
                />
            )
        }
    }

    return (
        <div className="app">
            <header className="header">
                <div className="header-content">
                    <div className="logo">
                        <div className="logo-icon">🎓</div>
                        <span className="logo-text">TutorIA</span>
                    </div>
                    <div className="user-info">
                        <div className="user-avatar">{userInitial}</div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '2px' }}>
                            <span className="user-name">{userName}</span>
                            {isInstructor && (
                                <span style={{ fontSize: '11px', color: '#7c3aed', fontWeight: '600' }}>
                                    👨‍🏫 Instructor
                                </span>
                            )}
                            {courseName && (
                                <span style={{ fontSize: '11px', color: '#64748b' }}>
                                    📚 {courseName}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            <main className="main-content">
                {!isInstructor && resourceConfig?.mode === 'tutor' && (
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
                )}

                {mainContent}
            </main>
        </div>
    )
}
