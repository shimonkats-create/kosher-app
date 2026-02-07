import streamlit as st
import PIL.Image
import google.generativeai as genai
from datetime import datetime

# הגדרות דף ועיצוב CSS מותאם אישית
st.set_page_config(page_title="סורק כשרות AI", page_icon="🛒", layout="centered")

st.markdown("""
    <style>
    /* עיצוב כללי לימין לשמאל */
    .main { text-align: right; direction: rtl; }
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
    }
    /* עיצוב כרטיסיית התוצאה */
    .result-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-right: 5px solid #4CAF50;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ניהול זיכרון היסטוריה
if "history" not in st.session_state:
    st.session_state.history = []

# בדיקת מפתח API
if "GEMINI_KEY" not in st.secrets:
    st.error("חסר מפתח API! הגדר אותו ב-Settings -> Secrets")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_KEY"])

@st.cache_resource
def get_model():
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = next((m for m in models if 'flash' in m), models[0])
    return genai.GenerativeModel(model_name)

model = get_model()

# תפריט צד
with st.sidebar:
    st.title("🕒 היסטוריה")
    if st.button("🗑️ נקה היסטוריה"):
        st.session_state.history = []
        if "last_result" in st.session_state: del st.session_state.last_result
        st.rerun()
    st.markdown("---")
    for i, item in enumerate(reversed(st.session_state.history)):
        if st.button(f"סריקה: {item['time']}", key=f"hist_{i}"):
            st.session_state.last_result = item

st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🛒 סורק רכיבים חכם</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = PIL.Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button('🚀 נתח מוצר עכשיו'):
        with st.spinner('מנתח...'):
            prompt = """
            נתח את התמונה בצורה טכנית ואובייקטיבית. אל תכתוב פסיקות הלכתיות.
            ענה בעברית לפי המבנה המדויק הבא:
            1. רכיבים: [אייקון] [הגדרה]
            2. סוג: [אייקון] [סוג]
            נימוק קצר: [משפט טכני אחד]
            ---
            [פירוט טכני מורחב ותרגום]
            """
            try:
                response = model.generate_content([prompt, img])
                parts = response.text.split("---")
                header = parts[0].strip()
                detail = parts[1].strip() if len(parts) > 1 else ""
                
                now = datetime.now().strftime("%H:%M")
                result_obj = {"time": now, "header": header, "detail": detail}
                st.session_state.history.append(result_obj)
                st.session_state.last_result = result_obj
            except Exception as e:
                st.error(f"שגיאה: {e}")

# תצוגת תוצאה מעוצבת
if "last_result" in st.session_state:
    res = st.session_state.last_result
    st.markdown(f"""
        <div class="result-card" style="direction: rtl; text-align: right;">
            <div style="font-size: 20px; line-height: 1.6;">
                {res['header'].replace('1. ', '<b>1. </b>').replace('2. ', '<br><b>2. </b>')}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if res['detail']:
        with st.expander("🔍 פירוט רכיבים ותרגום"):
            st.markdown(f"<div style='text-align: right; direction: rtl;'>{res['detail']}</div>", unsafe_allow_html=True)
