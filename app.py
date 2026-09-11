import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import google.generativeai as genai
from PIL import Image
import streamlit as st

# إعدادات الصفحة
st.set_page_config(
    page_title="المكتبة المركزية لجامعة تيبازة - مساعد الفهرسة لـ PMB",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# دالة لإعادة تعيين النموذج لبدء كتاب جديد
def reset_form():
  st.session_state.extracted_data = {}
  if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
  st.session_state.uploader_key += 1

# تهيئة المتغيرات عند التشغيل الأول
if "extracted_data" not in st.session_state:
  st.session_state.extracted_data = {}

if "uploader_key" not in st.session_state:
  st.session_state.uploader_key = 0

# تطبيق التنسيقات المخصصة
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }

    /* تعديل الهيدر المدمج لـ Streamlit */
    header[data-testid="stHeader"] {
        background-color: #0E3A43 !important;
        border-bottom: 1px solid #3FE0D0 !important;
    }
    
    header[data-testid="stHeader"] * {
        color: #ffffff !important;
    }

    /* تقليص الهوامش العلوية وزيادة الهامش السفلي لرؤية الأزرار بوضوح */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }

    /* خلفية التطبيق الرئيسية */
    .stApp {
        background-color: #1C889B;
        color: #ffffff;
    }
    
    /* القائمة الجانبية */
    [data-testid="stSidebar"] {
        background-color: #14616F;
        color: #ffffff;
    }
    
    /* إطار العنوان الرئيسي */
    .main-header-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .main-header {
        background-color: #0E424B;
        border: 2px solid #3FE0D0;
        border-radius: 12px;
        padding: 10px 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        width: 100%;
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 1.8rem;
        margin: 0;
        font-weight: 800;
    }
    
    /* تنسيق أزرار التبويبات */
    [data-testid="stTab"] {
        background-color: #0E424B !important;
        border: 1px solid #3FE0D0 !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        margin-left: 4px !important;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stTab"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }

    [data-testid="stTab"][aria-selected="true"] {
        background-color: #3FE0D0 !important;
        border-color: #ffffff !important;
    }

    [data-testid="stTab"][aria-selected="true"] p {
        color: #0E424B !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab-highlight-title"],
    [data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* عناوين الحقول والنصوص */
    label, .stMarkdown, p, span {
        color: #ffffff !important;
    }

    /* حقول الإدخال */
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }

    /* الأزرار */
    .stButton button, .stDownloadButton button, [data-testid="stFileUploader"] button {
        background-color: #0E424B !important;
        color: #ffffff !important;
        border: 1px solid #3FE0D0 !important;
        font-weight: bold !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }

    .stButton button:hover, .stDownloadButton button:hover, [data-testid="stFileUploader"] button:hover {
        background-color: #3FE0D0 !important;
        color: #0E424B !important;
        border-color: #ffffff !important;
    }

    /* مساحة فارغة في الأسفل */
    .bottom-spacer {
        height: 2cm;
        width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- الهيدر العلوي ---
header_col1, header_col2 = st.columns([0.6, 4], gap="small")

with header_col1:
  if os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=110)
  elif os.path.exists("11PNG.jpg"):
    st.image("11PNG.jpg", width=110)

with header_col2:
  st.markdown(
      """
    <div class="main-header-container">
        <div class="main-header">
            <h1>📚 مساعد الفهرسة والتحقق البصري لـ PMB</h1>
        </div>
    </div>
    """,
      unsafe_allow_html=True,
  )

# الشريط الجانبي
with st.sidebar:
  st.header("⚙️ إعدادات الذكاء الاصطناعي")
  api_key = st.text_input("أدخل مفتاح Gemini API Key:", type="password")
  st.info("احصل على مفتاح مجاني من: aistudio.google.com")

col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
  st.subheader("🖼️ المسح الضوئي / رفع صور الكتاب")

  uploaded_files = st.file_uploader(
      "اختر صور الكتاب (الغلاف، صفحة العنوان، صفحة الحقوق، الفهرس، إلخ):",
      type=["jpg", "jpeg", "png"],
      accept_multiple_files=True,
      key=f"file_uploader_{st.session_state.uploader_key}",
  )

  images = []
  if uploaded_files:
    st.write(f"📸 عدد الصور المرفوعة: {len(uploaded_files)}")
    cols = st.columns(min(len(uploaded_files), 3))
    for idx, file in enumerate(uploaded_files):
      img = Image.open(file)
      images.append(img)
      with cols[idx % 3]:
        st.image(img, caption=f"صفحة {idx+1}", use_container_width=True)

    if st.button(
        "🤖 تحليل كل الصفحات واستخراج البيانات",
        type="primary",
        use_container_width=True,
    ):
      if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح Gemini API في الشريط الجانبي أولاً.")
      else:
        try:
          with st.spinner(
              "جاري قراءة جميع الصفحات المرفوعة ومطابقة البيانات"
              " الببليوغرافية..."
          ):
            genai.configure(api_key=api_key)

            model = genai.GenerativeModel(
                "gemini-3.6-flash",
                generation_config={"response_mime_type": "application/json"},
            )

            prompt = """
                        قم بتحليل كافة الصور المرفوعة لهذا الكتاب (غلاف، صفحة عنوان، صفحة حقوق، مقدمة، فهرس) واستخرج الحقول التالية بصيغة JSON نقية فقط:
                        {
                          "title": "العنوان الرئيسي",
                          "subtitle": "العنوان الفرعي إن وجد",
                          "isbn": "الرقم الدولي المعياري ISBN",
                          "author": "اسم المؤلف الرئيسي",
                          "other_author": "المترجم أو المحرر إن وجد",
                          "publisher": "دار النشر",
                          "place": "مكان النشر",
                          "year": "سنة النشر",
                          "pages": "عدد الصفحات",
                          "keywords": "الكلمات المفتاحية / رؤوس الموضوعات مفصولة بـ فاصلة",
                          "abstract": "ملخص عام لمحتوى الكتاب أو مقدمته",
                          "notes": "ملاحظات توثيقية إضافية مثل رقم الطبعة"
                        }
                        إذا لم تجد حقلاً معيناً اتركه فارغاً "".
                        """

            content_payload = [prompt] + images
            response = model.generate_content(content_payload)

            data = json.loads(response.text.strip())
            st.session_state.extracted_data = data

            k = st.session_state.uploader_key
            st.session_state[f"title_{k}"] = data.get("title", "")
            st.session_state[f"subtitle_{k}"] = data.get("subtitle", "")
            st.session_state[f"isbn_{k}"] = data.get("isbn", "")
            st.session_state[f"author_{k}"] = data.get("author", "")
            st.session_state[f"other_{k}"] = data.get("other_author", "")
            st.session_state[f"pub_{k}"] = data.get("publisher", "")
            st.session_state[f"place_{k}"] = data.get("place", "")
            st.session_state[f"year_{k}"] = data.get("year", "")
            st.session_state[f"pages_{k}"] = data.get("pages", "")
            st.session_state[f"notes_{k}"] = data.get("notes", "")
            st.session_state[f"keywords_{k}"] = data.get("keywords", "")
            st.session_state[f"abstract_{k}"] = data.get("abstract", "")

            st.success("✅ تم تحليل كافة الصفحات واستخراج البيانات بنجاح!")
            st.rerun()

        except Exception as e:
          st.error(f"حدث خطأ أثناء القراءة: {e}")

  st.write("")
  if st.button(
      "🔄 تفريغ الصور والبدء من جديد",
      use_container_width=True,
      on_click=reset_form,
  ):
    st.toast("تم تفريغ الصور والحقول بنجاح!", icon="🧹")

with col_right:
  st.subheader("📋 حقول التحقق المطابقة لـ PMB")

  tab1, tab2, tab3, tab4 = st.tabs([
      "1️⃣ العام والمسؤولية",
      "2️⃣ النشر والتوزيع",
      "3️⃣ الوصف المادي",
      "4️⃣ التحليل الموضوعي",
  ])

  k = st.session_state.uploader_key

  with tab1:
    title_val = st.text_input("العنوان الرئيسي (200a)*", key=f"title_{k}")
    subtitle_val = st.text_input("العنوان الفرعي (200e)", key=f"subtitle_{k}")
    isbn_val = st.text_input("الرقم الدولي ISBN (010a)*", key=f"isbn_{k}")
    author_val = st.text_input(
        "المؤلف الرئيسي (200f / 700)", key=f"author_{k}"
    )
    other_author_val = st.text_input(
        "مؤلفون مشاركون / مترجم (701 / 702)", key=f"other_{k}"
    )

  with tab2:
    publisher_val = st.text_input("اسم الناشر (210c)*", key=f"pub_{k}")
    place_val = st.text_input("مكان النشر (210a)", key=f"place_{k}")
    year_val = st.text_input("سنة النشر (210d)", key=f"year_{k}")

  with tab3:
    pages_val = st.text_input("عدد الصفحات (215a)", key=f"pages_{k}")
    notes_val = st.text_area(
        "ملاحظات عامة والطبعة (300a)", height=80, key=f"notes_{k}"
    )

  with tab4:
    keywords_val = st.text_input(
        "الكلمات المفتاحية / رؤوس الموضوعات (610a)", key=f"keywords_{k}"
    )
    abstract_val = st.text_area(
        "ملخص الكتاب / المستخلص (330a)", height=90, key=f"abstract_{k}"
    )

  def generate_unimarc_xml():
    root = ET.Element("unimarc")
    notice = ET.SubElement(root, "notice")

    def add_field(tag, code, value):
      if value:
        f = ET.SubElement(notice, "field", tag=tag)
        s = ET.SubElement(f, "subfield", code=code)
        s.text = str(value)

    add_field("200", "a", title_val)
    add_field("200", "e", subtitle_val)
    add_field("010", "a", isbn_val)
    add_field("200", "f", author_val)
    add_field("701", "a", other_author_val)
    add_field("210", "c", publisher_val)
    add_field("210", "a", place_val)
    add_field("210", "d", year_val)
    add_field("215", "a", pages_val)
    add_field("300", "a", notes_val)
    add_field("610", "a", keywords_val)
    add_field("330", "a", abstract_val)

    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    return xml_str

  st.write("")

  col_btn1, col_btn2 = st.columns(2)
  with col_btn1:
    st.download_button(
        label="📥 تصدير ملف UNIMARC XML لـ PMB",
        data=generate_unimarc_xml(),
        file_name="pmb_notice.xml",
        mime="application/xml",
        use_container_width=True,
    )
  with col_btn2:
    st.button(
        "➕ إضافة كتاب جديد (تفريغ الحقول)",
        use_container_width=True,
        on_click=reset_form,
        type="secondary",
    )

st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True)
