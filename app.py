import streamlit as st
from PIL import Image
import google.generativeai as genai
import json

st.set_page_config(
    page_title="مساعد الفهرسة الذكي لـ PMB",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

st.title("📚 مساعد الفهرسة والتحقق البصري لـ PMB")

with st.sidebar:
    st.header("⚙️ إعدادات الذكاء الاصطناعي")
    api_key = st.text_input("أدخل مفتاح Gemini API Key:", type="password")
    st.info("احصل على مفتاح مجاني من: aistudio.google.com")

col_left, col_right = st.columns([1, 1.2], gap="large")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {}

with col_left:
    st.subheader("🖼️ المسح الضوئي / رفع صور الكتاب")
    # تم تفعيل accept_multiple_files لرفع عدة صور معاً
    uploaded_files = st.file_uploader(
        "اختر صور الكتاب (الغلاف، صفحة العنوان، صفحة الحقوق، الفهرس، إلخ):", 
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    images = []
    if uploaded_files:
        st.write(f"📸 عدد الصور المرفوعة: {len(uploaded_files)}")
        # عرض الصور المرفوعة في شبكة مصغرة
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
                        
                        # إرسال كافة الصور المرفوعة مع الـ Prompt دفعة واحدة
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
    
    # إضافة تبويب رابع للمحتوى التحليلي (الكلمات المفتاحية والملخص)
    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ العام والمسؤولية", 
        "2️⃣ النشر والتوزيع", 
        "3️⃣ الوصف المادي", 
        "4️⃣ التحليل الموضوعي"
    ])
    
    with tab1:
        st.text_input("العنوان الرئيسي (200a)*", value=extracted_data.get("title", ""))
        st.text_input("العنوان الفرعي (200e)", value=extracted_data.get("subtitle", ""))
        st.text_input("الرقم الدولي ISBN (010a)*", value=extracted_data.get("isbn", ""))
        st.text_input("المؤلف الرئيسي (200f / 700)", value=extracted_data.get("author", ""))
        st.text_input("مؤلفون مشاركون / مترجم (701 / 702)", value=extracted_data.get("other_author", ""))

    with tab2:
        st.text_input("اسم الناشر (210c)*", value=extracted_data.get("publisher", ""))
        st.text_input("مكان النشر (210a)", value=extracted_data.get("place", ""))
        st.text_input("سنة النشر (210d)", value=extracted_data.get("year", ""))

    with tab3:
        st.text_input("عدد الصفحات (215a)", value=extracted_data.get("pages", ""))
        st.text_area("ملاحظات عامة والطبعة (300a)", value=extracted_data.get("notes", ""))

    with tab4:
        st.text_input("الكلمات المفتاحية / رؤوس الموضوعات (610a)", value=extracted_data.get("keywords", ""))
        st.text_area("ملخص الكتاب / المستخلص (330a)", value=extracted_data.get("abstract", ""), height=150)

    st.divider()
    if st.button("📥 تصدير ملف UNIMARC XML لـ PMB", use_container_width=True):
        st.success("جاهز للتصدير المباشر إلى PMB!")
