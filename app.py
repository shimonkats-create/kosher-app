import streamlit as st
import PIL.Image
import google.generativeai as genai
from datetime import datetime
import io

# הגדרות דף
st.set_page_config(page_title="סורק כשרות מהיר", page_icon="⚡", layout="centered")

if "history" not in st.session_state:
    st.session_state.history = []

if "GEMINI_KEY" not in st.secrets:
    st.error("Missing API Key in Secrets!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_KEY"])

# מנגנון בחירת מודל חכם - פותר את שגיאת ה-404
@st.cache_resource
def get_model():
    # סריקה של כל המודלים הזמינים בחשבון שלך
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # עדיפות ראשונה: מודל flash (מהיר)
    # עדיפות שנייה: מודל pro
    # עדיפות שלישית: המודל הראשון ברשימה
    selected_model = next((m for m in available_models if 'flash' in m), 
                          next((m for m in available_models if 'pro' in m), 
                          available_models[0]))
    
    return genai.GenerativeModel(selected_model)

model = get_model()

def process_image_fast(uploaded_file):
    img = PIL.Image.open(uploaded_file)
    if img.mode != 'RGB': img = img.convert('RGB')
    img.thumbnail((800, 800))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=75)
    buffer.seek(0)
    return PIL.Image.open(buffer)

# תפריט צד
with st.sidebar:
    st.title("🕒 היסטוריה")
    if st.button("🗑️ נקה"):
        st.session_state.history = []
        if "last_result" in st.session_state: del st.session_state.last_result
        st.rerun()
    st.markdown("---")
    for i, item in enumerate(reversed(st.session_state.history)):
        if st.button(f"{item['time']} - סריקה", key=f"hist_{i}"):
            st.session_state.last_result = item

st.markdown("<h1 style='text-align: right;'>⚡ סורק כשרות מהיר</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("צלם רכיבים", type=["jpg", "jpeg", "png"])

# ניקוי תוצאה קודמת בהעלאה חדשה
if uploaded_file and "last_processed" in st.session_state and st.session_state.last_processed != uploaded_file.name:
    if "last_result" in st.session_state:
        del st.session_state.last_result

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    
    if "last_processed" not in st.session_state or st.session_state.last_processed != uploaded_file.name:
        with st.spinner('מנתח...'):
            fast_img = process_image_fast(uploaded_file)
            
            prompt = """
            Technical ingredients analysis. Bold suspicious items.
            Format exactly:
            1. רכיבים: [icon] [status]
            2. סוג: 🥦 פרווה / 🥛 חלבי / 🍖 בשרי
            נימוק: [short]
            ---
            [Hebrew full list, suspicious in **bold**]
            """
            try:
                response = model.generate_content([prompt, fast_img])
                parts = response.text.split("---")
                header = parts[0].strip()
                detail = parts[1].strip() if len(parts) > 1 else ""
                
                now = datetime.now().strftime("%H:%M")
                result_obj = {"time": now, "header": header, "detail": detail}
                
                st.session_state.history.append(result_obj)
                st.session_state.last_result = result_obj
                st.session_state.last_processed = uploaded_file.name
                st.rerun()
                
            except Exception as e:
                st.error(f"שגיאה בניתוח: {e}")

if "last_result" in st.session_state:
    res = st.session_state.last_result
    st.markdown("---")
    st.markdown(f"<div style='text-align: right; direction: rtl; font-size: 18px; font-weight: bold;'>{res['header']}</div>", unsafe_allow_html=True)
    if res['detail']:
        with st.expander("רשימה מפורטת"):
            st.markdown(f"<div style='text-align: right; direction: rtl;'>{res['detail']}</div>", unsafe_allow_html=True)
