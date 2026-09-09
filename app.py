import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

# إعدادات الصفحة
st.set_page_config(
    page_title="مساعد الفهرسة الذكي لـ PMB",
    page_icon="📚",
    layout="wide"
)

# تطبيق التنسيقات المخصصة (الخلفية، وتوسيط العنوان في إطار)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }

    /* تغيير لون خلفية التطبيق بالكامل */
    .stApp {
        background-color: #1C889B;
        color: #ffffff;
    }
    
    /* تنسيق القائمة الجانبية لتتناسب مع المظهر */
    [data-testid="stSidebar"] {
        background-color: #14616F;
        color: #ffffff;
    }
    
    /* تنسيق العنوان الرئيسي وإطاره وتوسيطه */
    .main-header-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 2rem;
    }
    .main-header {
        background-color: #0E424B;
        border: 2px solid #3FE0D0;
        border-radius: 15px;
        padding: 15px 40px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        margin: 0;
    }
    
    label, .stMarkdown, p, span {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# عرض العنوان الرئيسي في منتصف الصفحة داخل إطار
st.markdown("""
<div class="main-header-container">
    <div class="main-header">
        <h1>📚 مساعد الفهرسة والتحقق البصري لـ PMB</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# الشريط الجانبي
with st.sidebar:
    st.header("⚙️ إعدادات الذكاء الاصطناعي")
    api_key = st.text_input("أدخل مفتاح Gemini API Key:", type="password")
    st.info("احصل على مفتاح مجاني من: aistudio.google.com")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {}

col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.subheader("🖼️ المسح الضوئي / رفع صور الكتاب")
    uploaded_files = st.file_uploader(
        "اختر صور الكتاب (الغلاف، صفحة العنوان، صفحة الحقوق، الفهرس، إلخ):", 
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
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
        
        if st.button("🤖 تحليل كل الصفحات واستخراج البيانات", type="primary", use_container_width=True):
            if not api_key:
                st.error("⚠️ يرجى إدخال مفتاح Gemini API في الشريط الجانبي أولاً.")
            else:
                try:
                    with st.spinner("جاري قراءة جميع الصفحات المرفوعة ومطابقة البيانات الببليوغرافية..."):
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        
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
                        إذا لم تجد حقلاً معيناً اتركه فارغاً. أخرج الناتج بصيغة JSON نقية فقط بدون أي مظاهر تنسيق markdown.
                        """
                        
                        content_payload = [prompt] + images
                        response = model.generate_content(content_payload)
                        
                        clean_json = response.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.extracted_data = json.loads(clean_json)
                        st.success("✅ تم تحليل كافة الصفحات واستخراج البيانات بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء القراءة: {e}")

extracted_data = st.session_state.extracted_data

with col_right:
    st.subheader("📋 حقول التحقق المطابقة لـ PMB")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ العام والمسؤولية", 
        "2️⃣ النشر والتوزيع", 
        "3️⃣ الوصف المادي", 
        "4️⃣ التحليل الموضوعي"
    ])
    
    with tab1:
        title_val = st.text_input("العنوان الرئيسي (200a)*", value=extracted_data.get("title", ""))
        subtitle_val = st.text_input("العنوان الفرعي (200e)", value=extracted_data.get("subtitle", ""))
        isbn_val = st.text_input("الرقم الدولي ISBN (010a)*", value=extracted_data.get("isbn", ""))
        author_val = st.text_input("المؤلف الرئيسي (200f / 700)", value=extracted_data.get("author", ""))
        other_author_val = st.text_input("مؤلفون مشاركون / مترجم (701 / 702)", value=extracted_data.get("other_author", ""))

    with tab2:
        publisher_val = st.text_input("اسم الناشر (210c)*", value=extracted_data.get("publisher", ""))
        place_val = st.text_input("مكان النشر (210a)", value=extracted_data.get("place", ""))
        year_val = st.text_input("سنة النشر (210d)", value=extracted_data.get("year", ""))

    with tab3:
        pages_val = st.text_input("عدد الصفحات (215a)", value=extracted_data.get("pages", ""))
        notes_val = st.text_area("ملاحظات عامة والطبعة (300a)", value=extracted_data.get("notes", ""))

    with tab4:
        keywords_val = st.text_input("الكلمات المفتاحية / رؤوس الموضوعات (610a)", value=extracted_data.get("keywords", ""))
        abstract_val = st.text_area("ملخص الكتاب / المستخلص (330a)", value=extracted_data.get("abstract", ""), height=150)

    # تصدير ملف XML
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

    st.divider()
    st.download_button(
        label="📥 تصدير ملف UNIMARC XML لـ PMB",
        data=generate_unimarc_xml(),
        file_name="pmb_notice.xml",
        mime="application/xml",
        use_container_width=True
    )
