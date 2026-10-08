from pypdf import PdfReader
from google import genai
import streamlit as st
import sys
import os

# تنظیم انکودینگ سیستم روی UTF-8
sys.stdout.reconfigure(encoding='utf-8')


# ۱. تنظیمات اولیه صفحه
st.set_page_config(
    page_title="دستیار هوشمند متن و فایل",
    page_icon="✨",
    layout="centered"
)

# ۲. تلاش برای خواندن کلید از اینترنت (Streamlit Cloud)
MY_API_KEY = ""
try:
    MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    pass

# ۳. اگر روی کامپیوتر شخصی هستید و کلید در Secrets نبود، در منوی سمت چپ کادر بگذار
if not MY_API_KEY or MY_API_KEY == "کلید_API_خود_را_اینجا_بگذارید":
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ تنظیمات اتصال")
    MY_API_KEY = st.sidebar.text_input(
        "کلید Google API خود را اینجا وارد کنید:", type="password")

# لیست مدل‌ها جهت بازخوانی خودکار در صورت ترافیک
MODELS_TO_TRY = [
    'gemini-3.8-flash',
    'gemini-3.7-flash',
    'gemini-3.6-flash',
    'gemini-3.5-flash'
]

# تابع استخراج متن از فایل PDF


def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    return extracted_text

# تابع هوشمند ارسال درخواست با قابلیت سوئیچ خودکار در صورت شلوغی


def generate_content_safe(client, prompt):
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                continue
            else:
                raise e
    raise Exception(
        "سرورهای گوگل در حال حاضر شلوغ هستند. لطفاً چند ثانیه دیگر مجدداً تلاش کنید.")


# استایل‌های CSS سفارشی
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;600;800&display=swap');

    html, body, [class*="css"], div, span, input, textarea, button {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
        text-align: right;
    }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        margin-bottom: 25px;
    }
    .main-header h1 {
        color: white !important;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .stTextArea textarea {
        border-radius: 12px !important;
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        font-size: 15px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        background-color: #1e293b;
        color: #cbd5e1;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
    }

    .stButton button {
        width: 100%;
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-2px);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# هدر برنامه
st.markdown("""
    <div class="main-header">
        <h1>✨ دستیار هوشمند متن و فایل</h1>
        <p>خلاصه‌سازی و پرسش/پاسخ از متن یا فایل‌های PDF و TXT</p>
    </div>
""", unsafe_allow_html=True)

# بخش آپلود فایل
uploaded_file = st.file_uploader(
    "📂 فایل PDF یا TXT خود را آپلود کنید (اختیاری):", type=["pdf", "txt"])

# کادر ورود متن دستی
manual_text = st.text_area("📄 یا متن خود را به صورت دستی اینجا وارد کنید:", height=180,
                           placeholder="متن مورد نظر را اینجا بنویسید یا فایل فوق را آپلود کنید...")

# تعیین متن نهایی برای پردازش
final_text = ""

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".pdf"):
            final_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            final_text = uploaded_file.read().decode("utf-8")
        st.info(f"✅ فایل با موفقیت خوانده شد ({len(final_text)} کاراکتر).")
    except Exception as e:
        st.error(f"خطا در خواندن فایل: {e}")
else:
    final_text = manual_text

# بررسی اینکه آیا کلید API وارد شده است یا خیر
if not MY_API_KEY:
    st.warning(
        "👈 لطفاً کلید Google API خود را در منوی سمت چپ (Sidebar) وارد کنید تا برنامه فعال شود.")
else:
    client = genai.Client(api_key=MY_API_KEY)

    tab1, tab2 = st.tabs(["📝 خلاصه سازی", "❓ پرسش و پاسخ"])

    # --- بخش خلاصه سازی ---
    with tab1:
        st.write("---")
        if st.button("🚀 خلاصه‌سازی متن / فایل"):
            if final_text.strip() == "":
                st.warning(
                    "لطفاً ابتدا فایلی آپلود کنید یا متنی در کادر بنویسید!")
            else:
                with st.spinner("در حال تحلیـل و خلاصه‌سازی..."):
                    try:
                        prompt = f"متن زیر را به زبان فارسی در ۳ تا ۵ نقطه کلیدی، مرتب و شیک خلاصه کن:\n\n{final_text}"
                        result_text = generate_content_safe(client, prompt)
                        st.success("📌 خلاصه متن:")
                        st.markdown(result_text)
                    except Exception as err:
                        st.error(f"⚠️ خطای ارتباط با سرور: {err}")

    # --- بخش پرسش و پاسخ ---
    with tab2:
        st.write("---")
        question = st.text_input("💬 سوال خود را درباره متن یا فایل آپلودشده بپرسید:",
                                 placeholder="مثلاً: موضوع اصلی این فایل چیست؟")
        if st.button("🔍 یافتن پاسخ"):
            if final_text.strip() == "" or question.strip() == "":
                st.warning("لطفاً متن/فایل و هم سوال خود را وارد کنید!")
            else:
                with st.spinner("در حال جستجوی پاسخ..."):
                    try:
                        prompt = f"بر اساس متن زیر به سوال پاسخ بده. اگر پاسخ در متن نیست بگو 'پاسخ در متن یافت نشد'.\n\nمتن:\n{final_text}\n\nسوال:\n{question}"
                        result_text = generate_content_safe(client, prompt)
                        st.success("💡 پاسخ هوش مصنوعی:")
                        st.markdown(result_text)
                    except Exception as err:
                        st.error(f"⚠️ خطای ارتباط با سرور: {err}")
