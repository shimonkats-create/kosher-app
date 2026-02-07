import streamlit as st
import PIL.Image
import google.generativeai as genai

# הגדרות דף
st.set_page_config(page_title="סורק כשרות AI", page_icon="🛒", layout="centered")

# בדיקת מפתח API
if "GEMINI_KEY" not in st.secrets:
    st.error("חסר מפתח API! הגדר אותו ב-Settings -> Secrets של Streamlit")
    st.stop()

# חיבור ל-Gemini
genai.configure(api_key=st.secrets["GEMINI_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

st.markdown("<h1 style='text-align: right;'>🔍 ניתוח רכיבים טכני</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("צלם או העלה תמונה של הרכיבים", type=["jpg", "jpeg", "png"])

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
                
                st.markdown("---")
                st.markdown(f"<div style='text-align: right; direction: rtl; font-size: 18px; font-weight: bold;'>{parts[0]}</div>", unsafe_allow_html=True)
                
                if len(parts) > 1:
                    with st.expander("לפרטים נוספים ונימוק מפורט"):
                        st.markdown(f"<div style='text-align: right; direction: rtl;'>{parts[1]}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"שגיאה בניתוח: {e}")
