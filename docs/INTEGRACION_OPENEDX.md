# Integración del Tutor LTI con Open edX

## 📋 Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Configuración del Servidor](#paso-1-configuración-del-servidor)
3. [Registro en Open edX](#paso-2-registro-en-open-edx)
4. [Agregar a un Curso](#paso-3-agregar-a-un-curso)
5. [Configuración Avanzada](#configuración-avanzada)

---

## Requisitos Previos

- ✅ Instancia de Open edX funcionando (Tutor, Devstack, o producción)
- ✅ Servidor con el Tutor LTI corriendo (backend + frontend)
- ✅ URL pública accesible (para producción) o ngrok (para desarrollo)
- ✅ Acceso de administrador a Open edX

---

## Paso 1: Configuración del Servidor

### 1.1 Para Desarrollo (con ngrok)

```bash
# Instalar ngrok (si no lo tienes)
# Windows: scoop install ngrok
# O descargar de https://ngrok.com/download

# Exponer el backend
ngrok http 5000
```

Obtendrás una URL como: `https://abc123.ngrok-free.app`

### 1.2 Actualizar Variables de Entorno

Edita `backend/.env`:

```env
# URL de tu servidor (reemplaza con tu URL de ngrok o producción)
LTI_TOOL_URL=https://abc123.ngrok-free.app

# URL del frontend (puede ser la misma o diferente)
FRONTEND_URL=http://localhost:3000

# Tu API key de OpenAI (obligatorio para IA funcional)
OPENAI_API_KEY=sk-tu-api-key-aqui
```

### 1.3 Reiniciar el Backend

```bash
cd backend
# Detener el servidor actual (Ctrl+C)
./venv/Scripts/python app.py
```

---

## Paso 2: Registro en Open edX

### Opción A: Usando Django Admin (Método Recomendado)

#### 2.1 Acceder al Admin de Django

```
https://tu-openedx.com/admin
```

Inicia sesión con tu cuenta de superusuario.

#### 2.2 Crear un LTI Consumer

1. Ve a **LTI_PROVIDER** > **LTI Consumers** (o similar según tu versión)
2. Click en **Add LTI Consumer**
3. Completa los campos:

| Campo | Valor |
|-------|-------|
| **Consumer Name** | Tutor Virtual IA |
| **Consumer Key** | `tutor-lti-key` |
| **Consumer Secret** | `tu-secreto-seguro` (genera uno aleatorio) |

4. Guarda el consumer

#### 2.3 Crear Configuración LTI 1.3 (Open edX Quince+)

Para versiones más recientes con LTI 1.3:

1. Ve a **LTI_CONSUMER** > **LTI 1.3 Tools**
2. Click en **Add LTI 1.3 Tool**
3. Completa:

| Campo | Valor |
|-------|-------|
| **Tool Name** | Tutor Virtual IA |
| **Tool URL** | `https://tu-servidor/lti/launch` |
| **OIDC Login URL** | `https://tu-servidor/lti/login` |
| **Tool Public JWK URL** | `https://tu-servidor/lti/jwks` |
| **Deployment ID** | `1` |

4. Después de guardar, anota el **Client ID** generado

### Opción B: Usando Configuration JSON

1. Accede al endpoint de configuración:
   ```
   https://tu-servidor/lti/config.json
   ```

2. Copia el JSON generado

3. En Open edX Admin, ve a **LTI Consumer** > **LTI 1.3 Tools**

4. Usa la opción **Import from JSON** y pega el contenido

---

## Paso 3: Agregar a un Curso

### 3.1 Abrir Studio

```
https://studio.tu-openedx.com
```

### 3.2 Crear/Editar un Curso

1. Abre el curso donde quieres agregar el tutor
2. Ve a una unidad de contenido

### 3.3 Agregar Componente LTI

1. Click en **Advanced** > **LTI Consumer**
2. Configura el componente:

```
LTI ID: tutor-lti-key
LTI URL: https://tu-servidor/lti/launch
LTI Launch Target: New Window (o Inline Frame)
Custom Parameters: (opcional)
  - context_title=$Context.title
  - user_id=$User.id
```

### 3.4 Publicar

1. Click en **Publish** para hacer visible el componente
2. Los estudiantes ahora verán el Tutor Virtual en esa unidad

---

## Paso 4: Actualizar Backend con Credenciales

Una vez que tengas el Client ID de Open edX, actualiza `backend/.env`:

```env
# Configuración LTI obtenida de Open edX
LTI_ISSUER=https://tu-openedx.com
LTI_CLIENT_ID=el-client-id-generado
LTI_DEPLOYMENT_ID=1
LTI_JWKS_URL=https://tu-openedx.com/.well-known/jwks.json
LTI_AUTH_URL=https://tu-openedx.com/lti/authorize
LTI_TOKEN_URL=https://tu-openedx.com/oauth2/access_token
```

---

## Configuración Avanzada

### Personalizar el Contexto del Tutor

Puedes pasar parámetros personalizados desde Open edX:

En el componente LTI de Studio, agrega Custom Parameters:

```
topic=Matemáticas
course_level=intermedio
allow_hints=true
```

### Enviar Calificaciones a Open edX (AGS)

El tutor puede enviar calificaciones automáticamente. Asegúrate de:

1. Habilitar **LTI Assignment and Grade Services** en Open edX
2. Configurar el componente LTI como "graded"

### Seguridad en Producción

Para producción, asegúrate de:

1. **Usar HTTPS** en ambos servidores
2. **Generar claves RSA** para firmar tokens JWT:
   ```bash
   openssl genrsa -out private.pem 2048
   openssl rsa -in private.pem -pubout -out public.pem
   ```
3. **Validar tokens JWT** correctamente (el código actual tiene validación deshabilitada para desarrollo)

---

## Troubleshooting

### El tutor no carga

1. Verifica que la URL del servidor sea accesible desde el browser
2. Revisa la consola del navegador (F12) por errores CORS
3. Confirma que las URLs en `.env` coinciden con las de Open edX

### Error "Invalid state"

1. Asegúrate de que las cookies de sesión funcionan
2. Verifica que `SECRET_KEY` sea consistente

### La IA no responde

1. Confirma que `OPENAI_API_KEY` está configurado
2. Verifica que tienes créditos en tu cuenta de OpenAI

### Errores de CORS

Agrega la URL de Open edX a la configuración CORS en `app.py`:

```python
CORS(app, 
     origins=[
         app.config.get('FRONTEND_URL'),
         'https://tu-openedx.com'
     ],
     supports_credentials=True)
```

---

## Diagrama de Flujo LTI

```
┌─────────────┐     1. Click en Tutor     ┌─────────────┐
│   Open edX  │ ────────────────────────► │   Backend   │
│    (LMS)    │                           │  /lti/login │
└─────────────┘                           └──────┬──────┘
       ▲                                         │
       │                                         │ 2. Redirect
       │                                         ▼
       │ 3. Auth Token              ┌─────────────────────┐
       └────────────────────────────│  Open edX OIDC Auth │
                                    └──────────┬──────────┘
                                               │
                                               │ 4. id_token
                                               ▼
                                    ┌─────────────────────┐
                                    │     /lti/launch     │
                                    │   Valida token      │
                                    │   Crea sesión       │
                                    └──────────┬──────────┘
                                               │
                                               │ 5. Redirect
                                               ▼
                                    ┌─────────────────────┐
                                    │      Frontend       │
                                    │   Tutor Virtual     │
                                    └─────────────────────┘
```

---

## Recursos Adicionales

- [LTI 1.3 Specification](https://www.imsglobal.org/spec/lti/v1p3/)
- [Open edX LTI Documentation](https://edx.readthedocs.io/projects/open-edx-building-and-running-a-course/en/latest/exercises_tools/lti_component.html)
- [PyLTI1p3 Library](https://github.com/dmitry-viskov/pylti1.3)
