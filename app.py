import streamlit as st
from google import genai
from google.genai import types
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from PIL import Image

# إعدادات الصفحة
st.set_page_config(
    page_title="مساعد الفهرسة الذكي لـ PMB",
    page_icon="📚",
    layout="wide"
)

# تطبيق التنسيقات المخصصة (الخلفية، وتوسيط العنوان في إطار)
st.markdown("""
<style>
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
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين إضاءة النصوص داخل الحقول */
    label, .stMarkdown {
        color: #ffffff !important;
    }
</style>
""", unsafe_unsafe_html=True)

# عرض العنوان الرئيسي في منتصف الصفحة داخل إطار
st.markdown("""
<div class="main-header-container">
    <div class="main-header">
        <h1>📚 مساعد الفهرسة والتحقق البصري لـ PMB</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# الشريط الجانبي لإدخال المفتاح
st.sidebar.title("⚙️ إعدادات الذكاء الاصطناعي")
api_key = st.sidebar.text_input("أدخل مفتاح Gemini API Key:", type="password")
st.sidebar.markdown("[احصل على المفتاح مجاناً من: aistudio.google.com](https://aistudio.google.com)")

# تقسيم الشاشة إلى عمودين
col1, col2 = st.columns([1, 1])

with col2:
    st.header("📸 المسح الضوئي / رفع صور الكتاب")
    uploaded_files = st.file_uploader(
        "اختر صور الكتاب (الغلاف، صفحة العنوان، صفحة الحقوق، الفهرس، إلخ):", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )
    
    images = []
    if uploaded_files:
        for file in uploaded_files:
            img = Image.open(file)
            images.append(img)
        st.image(images, width=120, caption=[f.name for f in uploaded_files])

with col1:
    st.header("📋 تسجيل المطابقة لـ PMB")
    
    tab1, tab2, tab3, tab4 = st.tabs(["1️⃣ العام والمسؤولية", "2️⃣ النشر والتوزيع", "3️⃣ الوصف المادي", "4️⃣ التحليل الموضوعي"])
    
    with tab1:
        title = st.text_input("العنوان الرئيسي (200a)*")
        subtitle = st.text_input("العنوان الفرعي (200e)")
        isbn = st.text_input("الرقم الدولي ISBN (010a)*")
        author = st.text_input("المؤلف الرئيسي (200f / 700)")
        contributors = st.text_input("مؤلفون مشاركون / مترجم (701 / 702)")
        
    with tab2:
        publisher = st.text_input("دار النشر (210c)")
        pub_place = st.text_input("مكان النشر (210a)")
        pub_year = st.text_input("سنة النشر (210d)")
        edition = st.text_input("الطبعة (205a)")
        
    with tab3:
        pages = st.text_input("عدد الصفحات (215a)")
        illu = st.text_input("التوضيحات والرسوم (215c)")
        size = st.text_input("الحجم/الأبعاد (215d)")
        price = st.text_input("السعر (010d)")
        
    with tab4:
        keywords = st.text_input("الكلمات الرئيسية / العناوين (610a)")
        abstract = st.text_area("ملخص الكتاب / المستخلص (330a)", height=120)

    # زر استخراج البيانات بـ Gemini
    if st.button("✨ استخراج الفهرسة تلقائياً بالذكاء الاصطناعي", type="primary"):
        if not api_key:
            st.error("يرجى إدخال مفتاح Gemini API Key في القائمة الجانبية أولاً!")
        elif not images:
            st.warning("يرجى رفع صور الكتاب أولاً!")
        else:
            try:
                client = genai.Client(api_key=api_key)
                prompt = """
                أنت مفهرس مكتبات محترف خبير بنظام PMB ومعيار UNIMARC.
                قم بتحليل صور الكتاب المرفقة واستخرج الحقول التالية بدقة بصيغة JSON حصراً:
                {
                    "title": "",
                    "subtitle": "",
                    "isbn": "",
                    "author": "",
                    "contributors": "",
                    "publisher": "",
                    "pub_place": "",
                    "pub_year": "",
                    "edition": "",
                    "pages": "",
                    "illu": "",
                    "size": "",
                    "price": "",
                    "keywords": "",
                    "abstract": ""
                }
                """
                
                with st.spinner("جاري تحليل الصور واستخراج بيانات الفهرسة..."):
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt, *images]
                    )
                    
                    # تنظيف النتيجة
                    res_text = response.text.strip()
                    if res_text.startswith("```json"):
                        res_text = res_text[7:-3].strip()
                    elif res_text.startswith("```"):
                        res_text = res_text[3:-3].strip()
                        
                    data = json.loads(res_text)
                    st.success("تم استخراج البيانات بنجاح!")
                    st.json(data)
                    
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")

    # تصدير ملف UNIMARC XML
    def generate_unimarc_xml():
        root = ET.Element("unimarc")
        notice = ET.SubElement(root, "notice")
        
        def add_field(tag, code, value):
            if value:
                f = ET.SubElement(notice, "field", tag=tag)
                s = ET.SubElement(f, "subfield", code=code)
                s.text = str(value)
                
        add_field("200", "a", title)
        add_field("200", "e", subtitle)
        add_field("010", "a", isbn)
        add_field("200", "f", author)
        add_field("701", "a", contributors)
        add_field("210", "c", publisher)
        add_field("210", "a", pub_place)
        add_field("210", "d", pub_year)
        add_field("205", "a", edition)
        add_field("215", "a", pages)
        add_field("215", "c", illu)
        add_field("215", "d", size)
        add_field("010", "d", price)
        add_field("610", "a", keywords)
        add_field("330", "a", abstract)
        
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        return xml_str

    st.markdown("---")
    st.download_button(
        label="📥 تصدير ملف UNIMARC XML لـ PMB",
        data=generate_unimarc_xml(),
        file_name="pmb_notice.xml",
        mime="application/xml"
    )
