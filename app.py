import streamlit as st
import PIL.Image
import google.generativeai as genai
from datetime import datetime

# הגדרות דף
st.set_page_config(page_title="סורק כשרות AI", page_icon="🛒", layout="centered")

# ניהול זיכרון
if "history" not in st.session_state:
    st.session_state.history = []
if "scan_active" not in st.session_state:
    st.session_state.scan_active = False
if "current_img" not in st.session_state:
    st.session_state.current_img = None

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
    st.title("🕒 סריקות אחרונות")
    if st.button("🗑️ נקה היסטוריה"):
        st.session_state.history = []
        st.session_state.last_result = None
        st.session_state.scan_active = False
        st.session_state.current_img = None
        st.rerun()
    st.markdown("---")
    for i, item in enumerate(reversed(st.session_state.history)):
        if st.button(f"סריקה {len(st.session_state.history)-i}: {item['time']}", key=f"hist_{i}"):
            st.session_state.last_result = item
            st.session_state.scan_active = True
            # הערה: ההיסטוריה שומרת טקסט, התמונה המוצגת תהיה של הסריקה האחרונה בלבד

# כותרת והבהרה
st.markdown("<h1 style='text-align: right;'>🔍 ניתוח רכיבים אוטומטי</h1>", unsafe_allow_html=True)
st.markdown("""
    <p style='text-align: right; direction: rtl; color: white; font-size: 0.9em; margin-bottom: 20px; line-height: 1.6;'>
    שימו לב <span style='color: #ff4b4b; font-weight: bold; font-size: 1.2em;'>!</span> המערכת מנתחת רכיבים באופן טכני באמצעות בינה מלאכותית. אין לראות בתוצאות פסיקה הלכתית או הכשר למוצר. בכל ספק יש להיוועץ ברב או לבדוק את סמל הכשרות על גבי האריזה.
    </p>
    """, unsafe_allow_html=True)

# --- זרימת עבודה: סריקה או תוצאה ---

if not st.session_state.scan_active:
    # מצב 1: העלאת תמונה
    uploaded_file = st.file_uploader("צלם או העלה תמונה", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        img = PIL.Image.open(uploaded_file)
        st.session_state.current_img = img # שמירת התמונה בזיכרון
        st.image(img, use_container_width=True)
        
        with st.spinner('מנתח רכיבים...'):
            prompt = """
            נתח את התמונה טכנית. אל תכתוב פסיקות הלכתיות.
            משימות:
            1. זהה את כל הרכיבים.
            2. סמן ב-**בולד** כל רכיב עם חשש כשרות טכני.
            
            ענה בעברית לפי המבנה המדויק הבא:
            רכיבים: [🟢 לא נמצאו חשודים / 🟡 נמצאו רכיבים הדורשים בדיקה / 🔴 קיימים רכיבים לא כשרים]
            סוג: [🥦 פרווה / 🥛 חלבי / 🍖 בשרי]
            נימוק קצר: [משפט אחד טכני]
            ---
            [רשימת רכיבים מלאה מתורגמת לעברית, כשהחשודים מודגשים ב**בולד**]
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
                st.session_state.scan_active = True
                st.rerun()
                
            except Exception as e:
                st.error(f"שגיאה בניתוח: {e}")

else:
    # מצב 2: הצגת תוצאה + התמונה שנסרקה
    if "last_result" in st.session_state:
        # הצגת התמונה שנשמרה
        if st.session_state.current_img:
            st.image(st.session_state.current_img, use_container_width=True, caption="התמונה שנסרקה")
            
        res = st.session_state.last_result
        st.markdown("---")
        
        # תצוגת הכותרות והנימוק
        st.markdown(f"<div style='text-align: right; direction: rtl; font-size: 18px; line-height: 1.8;'>{res['header']}</div>", unsafe_allow_html=True)
        
        # לחצן לפרטים נוספים
        if res['detail']:
            with st.expander("לפרטים נוספים ורכיבים מודגשים"):
                st.markdown(f"<div style='text-align: right; direction: rtl;'>{res['detail']}</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # כפתור לסריקה חדשה
        if st.button("🔄 סריקה חדשה", use_container_width=True):
            st.session_state.last_result = None
            st.session_state.scan_active = False
            st.session_state.current_img = None
            st.rerun()
