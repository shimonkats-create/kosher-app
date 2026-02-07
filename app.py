import streamlit as st
import PIL.Image
import google.generativeai as genai
from datetime import datetime

# הגדרות דף
st.set_page_config(page_title="סורק כשרות AI", page_icon="🛒", layout="centered")

# ניהול זיכרון היסטוריה
if "history" not in st.session_state:
    st.session_state.history = []

# בדיקת מפתח API
if "GEMINI_KEY" not in st.secrets:
    st.error("חסר מפתח API ב-Secrets!")
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
    if st.button("🗑️ נקה הכל"):
        st.session_state.history = []
        if "last_result" in st.session_state: del st.session_state.last_result
        st.rerun()
    st.markdown("---")
    for i, item in enumerate(reversed(st.session_state.history)):
        if st.button(f"{item['time']} - סריקה", key=f"hist_{i}"):
            st.session_state.last_result = item

st.markdown("<h1 style='text-align: right;'>🔍 סורק רכיבים אוטומטי</h1>", unsafe_allow_html=True)

# העלאת קובץ - ברגע שמועלה קובץ, הקוד ימשיך הלאה אוטומטית
uploaded_file = st.file_uploader("צלם או העלה תמונה", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = PIL.Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    # בדיקה האם כבר עיבדנו את התמונה הזו כדי למנוע לופ של עיבוד
    if "last_processed" not in st.session_state or st.session_state.last_processed != uploaded_file.name:
        with st.spinner('מנתח רכיבים באופן אוטומטי...'):
            prompt = """
            נתח את התמונה טכנית. אל תפסוק הלכה.
            משימות: זהה רכיבים, בדוק מספרי E, והדגש ב**בולד** רכיבים דורשי בדיקה.
            
            השתמש בסמלים הבאים בדיוק:
            1. רכיבים: 🟢 לא נמצאו מצרכים לא כשרים / 🟡 נמצאו רכיבים הדורשים בדיקה / 🔴 קיימים רכיבים לא כשרים
            2. סוג: 🥦 פרווה / 🥛 חלבי / 🍖 בשרי
            
            נימוק: [סיכום קצר]
            ---
            [תרגום מלא עם הדגשות בבולד]
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
                st.session_state.last_processed = uploaded_file.name
            except Exception as e:
                st.error(f"שגיאה: {e}")

# הצגת התוצאה
if "last_result" in st.session_state:
    res = st.session_state.last_result
    st.markdown("---")
    st.markdown(f"<div style='text-align: right; direction: rtl; font-size: 18px; line-height: 1.6;'>{res['header']}</div>", unsafe_allow_html=True)
    if res['detail']:
        with st.expander("לרשימה המפורטת והדגשות"):
            st.markdown(f"<div style='text-align: right; direction: rtl;'>{res['detail']}</div>", unsafe_allow_html=True)
