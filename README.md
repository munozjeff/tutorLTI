# LTI AI Tutor para Open edX

Un tutor virtual inteligente con IA para integrar en Open edX usando LTI 1.3.

## 🚀 Características

- **Tutor Reactivo**: Responde preguntas de estudiantes en tiempo real
- **Tutor Predictivo**: Anticipa dificultades basándose en el rendimiento del estudiante
- **Análisis de Respuestas**: Detecta respuestas incorrectas y proporciona feedback detallado
- **Analytics de Aprendizaje**: Rastrea el progreso y predice el rendimiento
- **Integración LTI 1.3**: Compatible con Open edX y otros LMS

## 📁 Estructura del Proyecto

```
TutorLTI/
├── backend/                 # Servidor Python/Flask
│   ├── app.py              # Aplicación principal
│   ├── config.py           # Configuración
│   ├── models.py           # Modelos de base de datos
│   ├── routes/             # Rutas API
│   │   ├── lti.py          # Endpoints LTI 1.3
│   │   └── tutor.py        # Endpoints del tutor
│   └── services/           # Servicios
│       ├── ai_tutor.py     # Servicio de IA (OpenAI)
│       └── analytics.py    # Servicio de analíticas
├── frontend/               # Cliente React/Vite
│   ├── src/
│   │   ├── App.jsx         # Componente principal
│   │   ├── api.js          # Cliente API
│   │   └── index.css       # Estilos
│   └── index.html
└── README.md
```

## 🛠️ Instalación

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuración
copy .env.example .env

# Editar .env con tus configuraciones
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install
```

## ⚙️ Configuración

### Variables de Entorno (backend/.env)

```env
# Flask
SECRET_KEY=tu-clave-secreta-aqui
FLASK_ENV=development

# OpenAI
OPENAI_API_KEY=tu-api-key-de-openai

# LTI (configurar cuando integres con Open edX)
LTI_ISSUER=https://tu-instancia-openedx.com
LTI_CLIENT_ID=tu-client-id
LTI_DEPLOYMENT_ID=1
```

## 🚀 Ejecución

### Desarrollo

```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

El backend estará en `http://localhost:5000`
El frontend estará en `http://localhost:3000`

### Prueba sin LTI

Visita `http://localhost:5000/lti/dev-launch` para simular un launch LTI.

## 🔗 Integración con Open edX

### 1. Configurar el Tool en Open edX

En tu instancia de Open edX, ve a Admin > LTI Configuration y agrega:

- **Tool URL**: `http://tu-servidor:5000/lti/launch`
- **OIDC Login URL**: `http://tu-servidor:5000/lti/login`
- **Tool Configuration URL**: `http://tu-servidor:5000/lti/config.json`

### 2. Obtener Credenciales

Copia el Client ID y configúralo en tu `.env`

### 3. Agregar a un Curso

En Studio, agrega un componente LTI y selecciona el tutor.

## 📡 API Endpoints

### LTI
- `GET /lti/config.json` - Configuración LTI
- `POST /lti/login` - OIDC Login
- `POST /lti/launch` - LTI Launch
- `GET /lti/session` - Obtener sesión actual

### Tutor
- `POST /api/tutor/chat` - Enviar mensaje
- `POST /api/tutor/analyze-answer` - Analizar respuesta
- `GET /api/tutor/analytics` - Obtener analíticas
- `POST /api/tutor/hint` - Obtener hint predictivo

## 🤖 Funcionalidades del Tutor

### Chat Interactivo
```javascript
// Ejemplo de uso
const response = await sendMessage("¿Qué es la fotosíntesis?");
console.log(response.response); // Respuesta del tutor
console.log(response.predictive_hint); // Hint predictivo si aplica
```

### Análisis de Respuestas
```javascript
// Analizar una respuesta de examen
const analysis = await analyzeAnswer(
  "¿Cuál es la capital de Francia?",
  "Londres",
  "París"
);
console.log(analysis.is_correct); // false
console.log(analysis.feedback); // Explicación detallada
console.log(analysis.hints); // Pistas para mejorar
```

## 📊 Sistema Predictivo

El tutor analiza:
- Historial de respuestas
- Patrones de errores
- Tiempo de respuesta
- Áreas de dificultad

Y proporciona:
- Pistas proactivas antes de errores
- Materiales de refuerzo personalizados
- Alertas de intervención para instructores

## 🎨 Personalización

### Cambiar Colores (frontend/src/index.css)
```css
:root {
  --primary-500: #8b5cf6;  /* Color principal */
  --accent-500: #14b8a6;   /* Color de acento */
}
```

### Cambiar Prompt del Tutor (backend/services/ai_tutor.py)
```python
self.system_prompt = """Tu nuevo prompt aquí..."""
```

## 📝 Licencia

MIT License
