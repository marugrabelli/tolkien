# 📋 Especificación Funcional — AI Agent MVP

**Proyecto:** Tolkien AI Hub (Proof of Concept)  
**Versión:** 1.0  
**Tipo:** MVP / Maqueta demostrativa  
**Stack:** Python · Streamlit · Gemini API · Make · GitHub  

---

## 1. Objetivo del Producto

Demostrar que es posible construir un **agente de IA conversacional deployable y funcional** que:

- Resuelva consultas de usuarios de forma autónoma mediante un LLM.
- Detecte situaciones que requieran intervención humana y escale automáticamente.
- Notifique al equipo en tiempo real y registre los casos para seguimiento.
- Cuente con un panel básico de administración para acceder a la información.

El caso de uso concreto es un chatbot del Legendarium de Tolkien, pero la arquitectura aplica a cualquier dominio.

---

## 2. Actores del Sistema

| Actor | Descripción |
|---|---|
| **Usuario Final** | Persona que interactúa con el chatbot desde la interfaz pública |
| **Administrador** | Persona con credenciales que accede al panel de control |
| **Sistema HITL** | Componente automático que detecta escalados y notifica |
| **Operador Humano** | Persona del equipo que recibe alertas y da seguimiento |

---

## 3. Historias de Usuario

### Módulo: Chat Conversacional

---

**HU-001 — Interacción básica con el agente**

> Como **usuario final**, quiero poder escribir preguntas en lenguaje natural y recibir respuestas del agente, para obtener información sin necesidad de navegar por menús o formularios complejos.

**Criterios de aceptación:**
- El usuario puede ingresar texto libre en el campo de chat.
- El agente responde en el idioma configurado (alemán por defecto).
- El historial de la conversación se mantiene visible durante la sesión.
- El agente recuerda el contexto de los últimos 10 mensajes.

---

**HU-002 — Continuidad de contexto en la conversación**

> Como **usuario final**, quiero que el agente recuerde lo que le dije anteriormente en la misma sesión, para no tener que repetir información en cada mensaje.

**Criterios de aceptación:**
- El historial completo de la sesión se muestra en pantalla.
- Los últimos 10 turnos se envían al LLM como contexto.
- El historial persiste mientras no se reinicie la conversación.

---

**HU-003 — Reinicio de conversación**

> Como **usuario final**, quiero poder reiniciar la conversación desde cero, para comenzar una consulta nueva sin interferencia del historial anterior.

**Criterios de aceptación:**
- El botón "Reiniciar Conversación" está disponible en la barra lateral.
- Al hacer clic, se limpia el historial y todos los estados de la sesión.
- La interfaz vuelve al estado inicial inmediatamente.

---

### Módulo: Resiliencia del Sistema

---

**HU-004 — Tolerancia a fallos del LLM**

> Como **usuario final**, quiero que el sistema siga intentando responderme aunque el modelo de IA tenga problemas temporales, para no perder mi consulta por errores técnicos pasajeros.

**Criterios de aceptación:**
- Si el modelo primario falla, el sistema intenta con el modelo de respaldo automáticamente.
- Se realizan hasta 3 intentos por modelo con backoff exponencial (1s, 2s, 4s).
- Si todos los intentos fallan, se muestra un mensaje de error claro al usuario.
- El error no rompe el flujo de la aplicación.

---

### Módulo: Escalado HITL (Human-in-the-Loop)

---

**HU-005 — Detección de consultas críticas**

> Como **operador humano**, quiero que el sistema detecte automáticamente cuando un usuario necesita atención especializada, para poder intervenir antes de que la situación escale por falta de respuesta adecuada.

**Criterios de aceptación:**
- El sistema analiza cada mensaje del usuario buscando palabras clave críticas definidas.
- Palabras trigger actuales: `humano`, `human`, `mensch`, `soporte`, `error`, `reclamacion`, `copyright`.
- Al detectarse una palabra trigger, el chat se pausa automáticamente.
- Se muestra un mensaje de advertencia al usuario informando la pausa.

**Palabras trigger (configurables en código):**
```python
criterios_criticos = {"humano", "human", "mensch", "soporte", "error", "reclamacion", "copyright"}
```

---

**HU-006 — Captura de datos de contacto en escalado**

> Como **usuario final**, cuando necesito ayuda de una persona real, quiero poder dejar mis datos fácilmente para que me contacten, sin tener que salir de la aplicación.

**Criterios de aceptación:**
- Tras el trigger, se muestra un formulario con campos: Nombre, Correo, Teléfono.
- Todos los campos son obligatorios.
- Al enviar, se muestra confirmación de recepción.
- No se puede enviar el formulario con campos vacíos.

---

**HU-007 — Notificación automática al equipo**

> Como **operador humano**, quiero recibir una alerta automática con los datos del usuario y el contexto de la conversación cuando hay un escalado, para poder dar seguimiento sin depender de procesos manuales.

**Criterios de aceptación:**
- Al enviarse el formulario, se dispara el webhook de Make en segundo plano.
- El payload incluye: timestamp, nombre, correo, teléfono, última consulta, historial de chat.
- El proceso es asíncrono (no bloquea la UI).
- Si el webhook falla, la operación continúa sin mostrar error al usuario.

**Payload del webhook:**
```json
{
  "alert_type": "HUMAN_INTERVENTION_REQUIRED",
  "timestamp": "2025-01-15 14:30:00",
  "user_name": "...",
  "user_email": "...",
  "user_phone": "...",
  "last_query": "...",
  "chat_history": [...]
}
```

---

**HU-008 — Registro persistente de casos críticos**

> Como **administrador**, quiero que todos los casos escalados queden registrados en un archivo, para poder hacer seguimiento histórico y analizar patrones.

**Criterios de aceptación:**
- Cada escalado se guarda en `consultas_criticas.csv`.
- Si el archivo no existe, se crea automáticamente con encabezados.
- Si ya existe, se agrega la nueva fila sin sobreescribir datos anteriores.
- Los campos registrados son: Fecha_Hora, Nombre, Correo, Telefono, Ultima_Consulta, Historial_Contexto.

---

### Módulo: Panel de Administración

---

**HU-009 — Acceso protegido al panel de administración**

> Como **administrador**, quiero acceder a funciones de gestión mediante credenciales, para que el área de control no esté expuesta públicamente.

**Criterios de aceptación:**
- El formulario de login está disponible en la barra lateral.
- Solo con usuario y contraseña correctos se accede al panel.
- Los intentos fallidos muestran mensaje de error.
- La sesión admin persiste durante la sesión de Streamlit.
- Existe un botón para cerrar sesión.

> **Nota de seguridad MVP:** Las credenciales están hardcodeadas (`admin/admin`). En producción deben migrarse a secrets seguros o un sistema de autenticación externo.

---

**HU-010 — Descarga de base de datos de casos críticos**

> Como **administrador**, quiero poder descargar el CSV de consultas críticas desde la interfaz, para trabajarlo en herramientas externas sin necesidad de acceso al servidor.

**Criterios de aceptación:**
- El botón de descarga solo aparece si el administrador está autenticado.
- El botón solo aparece si el archivo CSV existe.
- Si no hay casos registrados aún, se muestra un mensaje informativo.
- El archivo se descarga con el nombre `consultas_criticas.csv`.

---

## 4. Flujos Principales

### Flujo 1: Conversación estándar

```
Usuario escribe → Detección de trigger (negativo) → Llamada a Gemini API
→ Respuesta mostrada → Guardado en historial de sesión
```

### Flujo 2: Escalado HITL

```
Usuario escribe → Detección de trigger (positivo) → Chat pausado
→ Formulario de contacto → Usuario completa datos → Envío
→ [Background] CSV actualizado + Webhook disparado
→ Confirmación al usuario
```

### Flujo 3: Administración

```
Admin ingresa credenciales → Autenticación → Panel activo
→ [Si CSV existe] Botón de descarga disponible
→ Admin descarga archivo → Admin cierra sesión
```

---

## 5. Reglas de Negocio

| ID | Regla |
|---|---|
| RN-001 | El agente responde en alemán por defecto. Cambia de idioma solo si el usuario lo solicita explícitamente. |
| RN-002 | El contexto enviado al LLM se limita a los últimos 10 turnos para controlar costos de tokens. |
| RN-003 | La detección de triggers es case-insensitive y elimina signos de puntuación antes de comparar. |
| RN-004 | El formulario de escalado no puede enviarse con campos vacíos. |
| RN-005 | Las operaciones de logging y webhook se ejecutan en un hilo separado para no bloquear la UI. |
| RN-006 | El sistema intenta hasta 3 veces por modelo antes de declarar fallo total. |

---

## 6. Limitaciones del MVP (conocidas)

| Limitación | Impacto | Solución en Producción |
|---|---|---|
| Credenciales admin hardcodeadas | Riesgo de seguridad | OAuth / sistema de auth externo |
| CSV como almacenamiento | No escala | Base de datos relacional (PostgreSQL) |
| Sin autenticación de usuarios finales | Sin trazabilidad por usuario | Sistema de login / sesiones |
| Historial limitado a sesión Streamlit | Se pierde al recargar | Persistencia en DB |
| Palabras trigger hardcodeadas | Inflexible | Panel de configuración dinámico |
| Sin métricas ni observabilidad | Difícil de monitorear | Dashboard + logging estructurado |

---

## 7. Stack Técnico

| Componente | Tecnología |
|---|---|
| Frontend / Backend | Streamlit (Python) |
| LLM Principal | Google Gemini 1.5 Flash |
| LLM Fallback | Google Gemini 2.5 Flash |
| Automatización externa | Make (ex-Integromat) vía webhook |
| Almacenamiento de logs | CSV local (pandas) |
| Concurrencia | Python threading |
| Deploy | Streamlit Cloud + GitHub |

---

*Documento generado para el MVP v1.0 — sujeto a revisión en iteraciones futuras.*
