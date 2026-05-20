# 🧙‍♂️ AI Agent MVP — Tolkien Hub (Proof of Concept)

> **Chatbot inteligente con escalado HITL, panel de administración y notificaciones automáticas vía webhook.**  
> Construido con Streamlit · Gemini API · Make (webhook) · GitHub

---

## 📌 ¿Qué es este proyecto?

Este MVP demuestra cómo un **agente conversacional de IA** puede desplegarse rápidamente para resolver problemas reales en distintos contextos: soporte al cliente, asesoramiento especializado, atención en sitios web o sistemas internos.

El caso de uso elegido es un chatbot temático del **Legendarium de Tolkien**, pero la arquitectura subyacente es **reutilizable y escalable** para cualquier dominio: e-commerce, salud, educación, finanzas, etc.

---

## 🧱 Arquitectura del Sistema

```
Usuario
  │
  ▼
Streamlit (Frontend + Lógica)
  │
  ├──► Gemini API (LLM)
  │       └── Fallback automático entre modelos (gemini-1.5-flash / gemini-2.5-flash)
  │
  ├──► HITL Trigger (palabras críticas detectadas)
  │       └── Formulario de contacto → Background Worker
  │               ├── CSV local (log persistente)
  │               └── Make Webhook → Email/Notificación al equipo
  │
  └──► Panel Admin (autenticación básica)
          └── Descarga de CSV con consultas críticas
```

---

## ✨ Features del MVP

| Feature | Descripción |
|---|---|
| 💬 Chat conversacional | Historial de los últimos 10 mensajes enviados al LLM |
| 🌐 Multimodelo con fallback | Si un modelo falla, intenta el siguiente con backoff exponencial |
| 🚨 Escalado HITL | Detecta palabras clave críticas y pausa el bot para derivar a humano |
| 📋 Formulario de contacto | Captura nombre, correo y teléfono del usuario en caso de escalado |
| 📧 Webhook a Make | Dispara automatizaciones (email, Slack, CRM) cuando hay un caso crítico |
| 🗂️ Log en CSV | Todas las consultas críticas se registran localmente |
| 🔐 Panel Admin | Acceso protegido con contraseña para descargar el CSV |
| 🔄 Reset de sesión | Botón público para limpiar el estado de la conversación |

---

## 🚀 Cómo correrlo localmente

### Requisitos

- Python 3.9+
- Cuenta en [Google AI Studio](https://aistudio.google.com/) (Gemini API Key)
- Cuenta en [Make](https://make.com/) (opcional, para webhook)

### Instalación

```bash
git clone https://github.com/tu-usuario/tu-repo.git
cd tu-repo
pip install -r requirements.txt
```

### Configuración de secrets

Crear el archivo `.streamlit/secrets.toml`:

```toml
Gemini_API_key = "TU_API_KEY_AQUI"
MAKE_WEBHOOK_URL = "https://hook.make.com/TU_WEBHOOK"  # Opcional
```

### Ejecutar

```bash
streamlit run app.py
```

---

## ☁️ Deploy en Streamlit Cloud

1. Hacer fork o push del repositorio a GitHub.
2. Ingresar a [share.streamlit.io](https://share.streamlit.io/).
3. Conectar el repo y definir `app.py` como entry point.
4. Agregar los secrets en el panel de configuración de la app.

---

## 📁 Estructura del repositorio

```
📦 proyecto
 ┣ 📄 app.py                    # Aplicación principal
 ┣ 📄 requirements.txt          # Dependencias
 ┣ 📄 README.md                 # Este archivo
 ┣ 📄 FUNCTIONAL_SPEC.md        # Especificación funcional + historias de usuario
 ┣ 📄 .gitignore
 ┗ 📁 .streamlit/
    ┗ 📄 secrets.toml           # NO versionar — agregar al .gitignore
```

---

## ⚙️ Variables de entorno / Secrets

| Variable | Requerida | Descripción |
|---|---|---|
| `Gemini_API_key` | ✅ Sí | API Key de Google Gemini |
| `MAKE_WEBHOOK_URL` | ❌ Opcional | URL del webhook de Make para alertas |

---

## 🔮 Roadmap (escala productiva)

- [ ] Autenticación robusta (OAuth / JWT)
- [ ] Base de datos persistente (PostgreSQL / Supabase)
- [ ] Dashboard de métricas de conversación
- [ ] Soporte multiidioma dinámico
- [ ] Integración con CRM (HubSpot, Salesforce)
- [ ] Embeddings + RAG para base de conocimiento propia
- [ ] Panel de configuración del sistema prompt sin tocar código
- [ ] Tests unitarios y de integración

---

## 📄 Licencia

MIT — libre para uso, modificación y distribución con atribución.

---

*Desarrollado como MVP de demostración de capacidades en IA aplicada.*
