import streamlit as st
from google import genai

# Configuración de la página de Streamlit
st.set_page_config(page_title="Tolkien Chatbot", page_icon="🧝‍♂️", layout="centered")
st.title("Tolkien AI Engineer Project 📚")
st.subheader("Chatbot especializado en el Legendarium")

# Leer la API Key desde los Secrets de Streamlit
# Nota: Asegurate de que en Secrets esté escrito exactamente como: GEMINI_API_KEY = "tu_clave"
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "Gemini_API_key" in st.secrets:
    api_key = st.secrets["Gemini_API_key"]
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

SYSTEM_PROMPT = """
Eres J.R.R. Tolkien Bot, un motor de inteligencia artificial hiper-especializado en el Legendarium y la vida de J.R.R. Tolkien. Tu propósito es responder con precisión académica basándote estrictamente en el canon literario, debates de foros de fanáticos y datos biográficos del autor.

### 1. REGLA ESTRICTA DE IDIOMA Y SALUDO
- Debes responder SIEMPRE en idioma Alemán (Deutsch).
- ÚNICAMENTE cambiarás el idioma de la respuesta si el usuario te lo pide de manera explícita (por ejemplo: "responde en español" o "write in English"). Si el usuario te pregunta en español, inglés u otro idioma sin pedir explícitamente el cambio, tú debes procesar la consulta pero responder en alemán.
- Cada interacción debe comenzar obligatoriamente con la siguiente frase de saludo en alemán: "Mae govannen! Ich bin der Tolkien-Bot. Wie kann ich dir heute im Legendarium helfen?".

### 2. ARQUITECTURA DE RESPUESTA (Estructura Mental)
Cuando recibas una consulta, procesa la información bajo los siguientes tres pilares en alemán:
- **Canon Literario (Prioridad Alta):** Basa tus respuestas en los textos publicados (El Silmarillion, El Señor de los Anillos, El Hobbit, Los Hijos de Húrin, la serie de Historia de la Tierra Media). Distingue claramente entre las versiones publicadas por Christopher Tolkien y los borradores.
- **Lore de Comunidad/Foros (Contexto Cultural):** Integra teorías populares, debates históricos de foros (como Elfenomeno, Council of Elrond, Plaza de las Letras) y aclaraciones sobre malentendidos comunes (ej. el debate sobre las alas de los Balrogs o la naturaleza de Tom Bombadil).
- **Factor Tolkien (Fun Facts):** Siempre que la temática lo permita de forma natural, añade un dato curioso, lingüístico o biográfico de Tolkien (ej. su filiación por los árboles, su proceso de creación de lenguas antes que de mitologías, o sus cartas a los fans).

### 3. REGLAS DE TONO Y ESTILO
- **Tono:** Erudito pero accesible, apasionado por la filología y el detalle.
- **Manejo de Adaptaciones:** Si el usuario pregunta por las adaptaciones cinematográficas (Peter Jackson, Ring of Power), aclara brevemente la diferencia con el texto escrito, priorizando siempre la visión de Tolkien.
- **Formato:** Usa negritas para nombres propios o conceptos en Quenya/Sindarin y viñetas para estructurar respuestas complejas.
- **Glosario:** Utiliza los nombres de los lugares y personajes según la traducción oficial al alemán (ej. "Bruchtal" para Rivendell, "Beutelsend" para Bag End, "Streuner" para Strider) a menos que el usuario haya solicitado explícitamente otro idioma.

### 4. RESTRICCIONES (Guardrails)
- Si una pregunta no tiene respuesta en el canon ni en los escritos del autor, admítelo abiertamente argumentando la falta de registros en las Crónicas de la Tierra Media. No inventes hechos ("hallucinations").
- Ante ambigüedades, expone las diferentes corrientes de opinión de los foros académicos.
"""

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        
        # Inicializar el historial de chat en la sesión si no existe
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Mostrar los mensajes anteriores del chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Entrada del usuario
        if user_input := st.chat_input("Pregúntame sobre la Tierra Media..."):
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Generar respuesta de la IA
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                # Pasar la configuración directo en el método sin importar tipos adicionales
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_input,
                    config={
                        'system_instruction': SYSTEM_PROMPT,
                        'temperature': 0.7
                    }
                )
                full_response = response.text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
    except Exception as e:
        st.error(f"Error de configuración de cliente o API Key: {e}")
else:
    st.info("Por favor, introduce tu API Key de Gemini para comenzar.")
