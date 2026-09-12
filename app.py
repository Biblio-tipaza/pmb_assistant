import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import google.generativeai as genai
from PIL import Image
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والتنسيق التركوازي الأصلي
# ==========================================
st.set_page_config(
    page_title="مساعد الفهرسة والتحليل الآلي",
    layout="wide",
    initial_sidebar_state="expanded",
)

# استعادة ألوان خلفية الواجهة والأزرار التركوازية
st.markdown(
    """
    <style>
    /* خلفية التطبيق الرئيسية */
    .stApp {
        background-color: #177383 !important;
        color: white !important;
    }
    
    /* تنسيق أزرار Streamlit */
    .stButton>button, .stDownloadButton>button {
        background-color: #0f4c5c !important;
        color: #ffffff !important;
        border: 1px solid #2b9348 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #2b9348 !important;
        color: #ffffff !important;
        border-color: #ffffff !important;
    }

    /* حقول الإدخال والقوائم المنسدلة */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 6px !important;
    }
    
    label {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. الواجهة الرئيسية وحقول البيانات
# ==========================================
st.title("📚 مساعد الفهرسة والتحليل الآلي")
st.write("---")

col1, col2 = st.columns([1, 1])

with col1:
  st.subheader("📝 البيانات المستخرجة")

  title_val = st.text_input(
      "العنوان الرئيسي",
      value="دراسة قياسية لأثر التكنولوجيا المالية على النمو الاقتصادي في الجزائر",
  )
  subtitle_val = st.text_input("العنوان الفرعي (200e)", value="")
  isbn_val = st.text_input("الرقم الدولي ISBN (010a)", value="")
  author_val = st.text_input(
      "المؤلف الرئيسي (700 / 200f)", value="طارب ياسمين، بن مهيرة أسماء"
  )
  other_author_val = st.text_input(
      "مؤلفون مشاركون / مترجم (701 / 702)", value="د. بن شهيدة سارة (إشراف)"
  )
  publisher_val = st.text_input("ناشر / جامعة", value="جامعة تيبازة")
  year_val = st.text_input("السنة", value="2025-2026")

with col2:
  st.subheader("🖼️ معاينة الغلاف / الوثيقة")
  st.info("معاينة الوثيقة المعالجة عبر الذكاء الاصطناعي")

st.write("---")


# ==========================================
# 3. دالة توليد XML لـ PMB
# ==========================================
def generate_unimarc_xml():
  xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <unimarc>
        <notice>
            <datafield tag="200" ind1="1" ind2=" ">
                <subfield code="a">{title_val}</subfield>
                <subfield code="f">{author_val}</subfield>
            </datafield>
            <datafield tag="210" ind1=" " ind2=" ">
                <subfield code="d">{year_val}</subfield>
            </datafield>
        </notice>
    </unimarc>"""
  return xml_data.encode("utf-8")


# ==========================================
# 4. قسم التصدير وقائمة الخيارات المحدثة
# ==========================================
st.subheader("📤 اختر جهة تصدير الملف / البيانات:")

btn_col1, btn_col2 = st.columns([1, 1])

with btn_col1:
  export_option = st.selectbox(
      "جهة التصدير:",
      [
          "تصدير الملف لـ PMB (UNIMARC XML)",
          "تصدير البيانات لمذكرات الماستر",
          "تصدير البيانات لكتاب خارجي",
          "تصدير البيانات لمطبوعة جامعية",
          "تصدير البيانات لأطروحة دكتوراه",
      ],
      key="export_selector",
      label_visibility="collapsed",
  )

with btn_col2:
  urls = {
      "تصدير البيانات لمذكرات الماستر": (
          "https://bi-cu-tipaza.infinityfreeapp.com/add_data.php"
      ),
      "تصدير البيانات لكتاب خارجي": (
          "https://bi-cu-tipaza.infinityfreeapp.com/add_external_book.php"
      ),
      "تصدير البيانات لمطبوعة جامعية": (
          "https://bi-cu-tipaza.infinityfreeapp.com/add_publication.php"
      ),
      "تصدير البيانات لأطروحة دكتوراه": (
          "https://bi-cu-tipaza.infinityfreeapp.com/add_university_thesis.php"
      ),
  }

  if export_option == "تصدير الملف لـ PMB (UNIMARC XML)":
    st.download_button(
        label="📥 تحميل ملف UNIMARC XML",
        data=generate_unimarc_xml(),
        file_name="pmb_notice.xml",
        mime="application/xml",
        use_container_width=True,
    )
  else:
    export_payload = json.dumps({
        "title": title_val,
        "author": author_val,
        "supervisor": other_author_val,
        "year": year_val,
        "publisher": publisher_val,
    })

    target_link = urls[export_option]
    btn_title = f"🚀 {export_option}"

    if st.button(btn_title, use_container_width=True):
      js_cmd = f"""
            <script>
            navigator.clipboard.writeText({json.dumps(export_payload)}).then(function() {{
                window.open('{target_link}', '_blank');
            }});
            </script>
            """
      st.components.v1.html(js_cmd, height=0)
      st.toast("تم نسخ البيانات وفتح الواجهة بنجاح!", icon="📋")
