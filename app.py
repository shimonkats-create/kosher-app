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
    st.error("חסר מפתח API! הגדר אותו ב-Settings -> Secrets")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_KEY"])

@st.cache_resource
def get_model():
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = next((m for m in models if 'flash' in m), models[0])
    return genai.GenerativeModel(model_name)

model = get_model()

# תפריט צד להיסטוריה
with st.sidebar:
    st.title("🕒 סריקות אחרונות")
    if st.button("🗑️ נקה היסטוריה"):
        st.session_state.history = []
        if "last_result" in st.session_state: del st.session_state.last_result
        st.rerun()
    st.markdown("---")
    if not st.session_state.history:
        st.write("אין עדיין סריקות")
    for i, item in enumerate(reversed(st.session_state.history)):
        if st.button(f"סריקה {len(st.session_state.history)-i}: {item['time']}", key=f"hist_{i}"):
            st.session_state.last_result = item

st.markdown("<h1 style='text-align: right;'>🔍 ניתוח רכיבים אוטומטי</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("צלם או העלה תמונה", type=["jpg", "jpeg", "png"])

# --- החלק החדש למחיקת תצוגה קודמת ---
if uploaded_file:
    # אם העלינו קובץ חדש ששונה מהקובץ האחרון שעיבדנו - נמחק את התצוגה הישנה מיד
    if "last_processed" in st.session_state and st.session_state.last_processed != uploaded_file.name:
        if "last_result" in st.session_state:
            del st.session_state.last_result
# ---------------------------------------

if uploaded_file:
    img = PIL.Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if "last_processed" not in st.session_state or st.session_state.last_processed != uploaded_file.name:
        with st.spinner('מנתח רכיבים...'):
            prompt = """
            נתח את התמונה טכנית. אל תכתוב פסיקות הלכתיות.
            
            משימות ה"מוח":
            1. זהה את כל רשימת הרכיבים ומספרי ה-E.
            2. סמן ב-**בולד** (כוכביות) כל רכיב שיש בו חשש כשרות טכני (כמו ג'לטין, E471, E120 וכו').
            
            ענה בעברית לפי המבנה הבא:
            1. רכיבים: 🟢 לא נמצאו מצרכים לא כשרים / 🟡 חשש למצרכים לא כשרים במוצר / 🔴 קיימים מצרכים לא כשרים במוצר
            2. סוג: 🥦 פרווה / 🥛 חלבי / 🍖 בשרי
            
            נימוק קצר: [משפט טכני אחד על הרכיבים שהדגשת]
            ---
            [כאן רשום תרגום מלא של הרכיבים לעברית, כשהחשודים מודגשים ב**בולד**]
            """
            try:
                response = model.generate_content([prompt, img])
                full_res = response.text
                parts = full_res.split("---")
                
                header = parts[0].strip()
                detail = parts[1].strip() if len(parts) > 1 else ""
                
                now = datetime.now().strftime("%H:%M")
                result_obj = {"time": now, "header": header, "detail": detail}
                
                st.session_state.history.append(result_obj)
                st.session_state.last_result = result_obj
                st.session_state.last_processed = uploaded_file.name
                st.rerun() # מרענן את הדף כדי להציג את התוצאה החדשה בלבד
                
            except Exception as e:
                st.error(f"שגיאה בניתוח: {e}")

# הצגת התוצאה (תופיע רק אם יש תוצאה רלוונטית)
if "last_result" in st.session_state:
    res = st.session_state.last_result
    st.markdown("---")
    st.markdown(f"<div style='text-align: right; direction: rtl; font-size: 18px; font-weight: bold; line-height: 1.8;'>{res['header']}</div>", unsafe_allow_html=True)
    
    if res['detail']:
        with st.expander("לפרטים נוספים ורכיבים מודגשים"):
            st.markdown(f"<div style='text-align: right; direction: rtl;'>{res['detail']}</div>", unsafe_allow_html=True)
