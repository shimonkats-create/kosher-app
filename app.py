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

# מנגנון בחירת מודל אוטומטי למניעת שגיאת 404
@st.cache_resource
def get_model():
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # מחפש מודל flash, אם אין לוקח את הראשון ברשימה
    model_name = next((m for m in models if 'flash' in m), models[0])
    return genai.GenerativeModel(model_name)

model = get_model()

# תפריט צד להיסטוריה
with st.sidebar:
    st.title("🕒 סריקות אחרונות")
    if not st.session_state.history:
        st.write("אין עדיין סריקות")
    for i, item in enumerate(reversed(st.session_state.history)):
        if st.button(f"סריקה {len(st.session_state.history)-i}: {item['time']}", key=f"hist_{i}"):
            st.session_state.last_result = item

st.markdown("<h1 style='text-align: right;'>🔍 ניתוח רכיבים טכני</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("צלם או העלה תמונה", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = PIL.Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button('נתח רכיבים'):
        with st.spinner('מנתח נתונים...'):
            prompt = """
            נתח את התמונה בצורה טכנית ואובייקטיבית. אל תכתוב פסיקות הלכתיות.
            ענה בעברית לפי המבנה המדויק הבא:
            
            1. רכיבים: [אייקון] [הגדרה]
            2. סוג: [אייקון] [סוג]
            
            (הגדרות לבחירה):
            - רכיבים: 🟢 לא נמצאו מצרכים לא כשרים / 🟡 חשש למצרכים לא כשרים במוצר / 🔴 קיימים מצרכים לא כשרים במוצר
            - סוג: 🟢 פרווה / 🔵 חלבי / 🔴 בשרי
            
            נימוק קצר: [משפט טכני אחד]
            
            ---
            [כאן רשום את הנימוק המפורט: תרגום רכיבים ופירוט טכני ללא פסיקה]
            """
            try:
                response = model.generate_content([prompt, img])
                full_res = response.text
                parts = full_res.split("---")
                
                header = parts[0].strip()
                detail = parts[1].strip() if len(parts) > 1 else ""
                
                # שמירה להיסטוריה
                now = datetime.now().strftime("%H:%M")
                result_obj = {"time": now, "header": header, "detail": detail}
                st.session_state.history.append(result_obj)
                st.session_state.last_result = result_obj
                
            except Exception as e:
                st.error(f"שגיאה בניתוח: {e}")

# הצגת התוצאה האחרונה (מסריקה חדשה או מההיסטוריה)
if "last_result" in st.session_state:
    res = st.session_state.last_result
    st.markdown("---")
    st.markdown(f"<div style='text-align: right; direction: rtl; font-size: 18px; font-weight: bold; line-height: 1.8;'>{res['header']}</div>", unsafe_allow_html=True)
    
    if res['detail']:
        with st.expander("לפרטים נוספים ונימוק מפורט"):
            st.markdown(f"<div style='text-align: right; direction: rtl;'>{res['detail']}</div>", unsafe_allow_html=True)
