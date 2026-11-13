import streamlit as st
import os
import tempfile
import json
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
from modules.actions import (
    get_patient_info, reschedule_appointment, 
    get_today_appointments, check_inventory_shortages, update_lab_status
)
from modules.tts_engine import generate_audio
from modules.file_manager import get_incoming_files, process_image

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# --- 1. إعدادات الصفحة وتخصيص التصميم (CSS) ---
st.set_page_config(page_title="النظام الذكي للعيادة", page_icon="🦷", layout="wide")

st.markdown("""
<style>
    /* استيراد خط عربي احترافي */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif !important;
    }
    
    /* إخفاء عناصر Streamlit المزعجة */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* خلفية التطبيق */
    .stApp {
        background-color: #f4f7f6;
    }
    
    /* تصميم البطاقات (Cards) */
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-right: 5px solid #0ea5e9;
        margin-bottom: 20px;
    }
    
    /* تصميم زر المايكروفون ليكون بارزاً */
    .stAudioInput {
        background-color: #e0f2fe;
        border-radius: 15px;
        padding: 15px;
        border: 2px dashed #0ea5e9;
    }
    
    /* تصميم صناديق المعلومات */
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'database', 'clinic.db')

# --- دوال مساعدة ---
def get_all_patients():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pts = conn.execute('SELECT id, name FROM Patients').fetchall()
    conn.close()
    return pts

def get_inventory():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    items = conn.execute('SELECT * FROM Inventory').fetchall()
    conn.close()
    return items

def get_lab_work():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    lab = conn.execute('''
        SELECT Lab_Work.*, Patients.name 
        FROM Lab_Work JOIN Patients ON Lab_Work.patient_id = Patients.id
    ''').fetchall()
    conn.close()
    return lab

tools_schema = [
    {"type": "function", "function": {"name": "get_patient_info", "description": "تجهيز ملف المريض", "parameters": {"type": "object", "properties": {"patient_name": {"type": "string"}}, "required": ["patient_name"]}}},
    {"type": "function", "function": {"name": "reschedule_appointment", "description": "تغيير موعد", "parameters": {"type": "object", "properties": {"patient_name": {"type": "string"}, "new_date": {"type": "string"}, "new_time": {"type": "string"}}, "required": ["patient_name", "new_date", "new_time"]}}},
    {"type": "function", "function": {"name": "get_today_appointments", "description": "مواعيد اليوم", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "check_inventory_shortages", "description": "نواقص المخزون", "parameters": {"type": "object", "properties": {}}}}
]

def process_ai_request(user_text):
    if not client or api_key == "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx":
        return f"أهلاً دكتور. (وضع المحاكاة). لقد سمعتك تقول: '{user_text}'. سأقوم بتنفيذ طلبك فور تفعيل الرصيد."
        
    messages = [
        {"role": "system", "content": "أنت مساعد ذكي لطبيب أسنان محترف. لديك أدوات برمجية. استخدم الأداة المناسبة. أجب باللهجة السورية الشامية."},
        {"role": "user", "content": user_text}
    ]
    
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools_schema, tool_choice="auto")
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "get_patient_info": function_response = get_patient_info(function_args.get("patient_name"))
                elif function_name == "reschedule_appointment": function_response = reschedule_appointment(function_args.get("patient_name"), function_args.get("new_date"), function_args.get("new_time"))
                elif function_name == "get_today_appointments": function_response = get_today_appointments()
                elif function_name == "check_inventory_shortages": function_response = check_inventory_shortages()
                else: function_response = {"status": "error"}
                    
                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": json.dumps(function_response, ensure_ascii=False)})
                
            second_response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
            return second_response.choices[0].message.content
        else:
            return response_message.content
    except Exception as e:
        return f"أهلاً دكتور. (رصيد الـ API صفر). لقد تلقيت أمرك: '{user_text}'."

# --- واجهة المستخدم ---
st.markdown("<h1 style='text-align: center; color: #0369a1;'>🦷 النظام الذكي لإدارة العيادة</h1>", unsafe_allow_html=True)

# قسم الصور الواردة
incoming_files = get_incoming_files()
if incoming_files:
    st.warning(f"⚠️ يوجد {len(incoming_files)} صور أشعة جديدة تحتاج لفرز!")
    with st.expander("انقر هنا لفرز الصور الجديدة", expanded=True):
        patients = get_all_patients()
        patient_dict = {p['name']: p['id'] for p in patients}
        for img_path in incoming_files:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(img_path, caption="صورة واردة", use_container_width=True)
            with col2:
                selected_patient_name = st.selectbox("لمن هذه الصورة؟", list(patient_dict.keys()), key=f"sel_{img_path}")
                if st.button("حفظ وترتيب الصورة", key=f"btn_{img_path}"):
                    success, msg = process_image(img_path, patient_dict[selected_patient_name], selected_patient_name)
                    if success:
                        st.success("تم حفظ الصورة!")
                        st.rerun()

# تقسيم الشاشة إلى 3 تبويبات احترافية
tab1, tab2, tab3 = st.tabs(["🩺 المساعد الذكي", "📦 المخزون والمخبر", "📅 مواعيد اليوم"])

with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.subheader("📁 ملفات المرضى")
        patients = get_all_patients()
        if patients:
            selected_name = st.selectbox("عرض ملف:", [p['name'] for p in patients])
            info = get_patient_info(selected_name)
            if info['status'] == 'success':
                st.info(f"**الاسم:** {info['patient_name']} | **الحساسية:** {info['allergies']}")
                st.write(f"**الصور الشعاعية ({info['images_count']}):**")
                if info['images']:
                    for img_rel_path in info['images']:
                        full_path = os.path.join(BASE_DIR, img_rel_path)
                        if os.path.exists(full_path):
                            st.image(full_path, use_container_width=True)
                else:
                    st.write("لا توجد صور مرفقة.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.subheader("💬 المحادثة الصوتية")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and "audio_path" in msg and msg["audio_path"]:
                    st.audio(msg["audio_path"], format="audio/mp3")

        audio_value = st.audio_input("🎤 اضغط وتحدث...")
        if audio_value:
            with st.spinner("جاري الاستماع..."):
                transcribed_text = "شو مواعيدي اليوم؟" # محاكاة
                st.session_state.messages.append({"role": "user", "content": f"🎤 {transcribed_text}"})
                with st.chat_message("user"):
                    st.markdown(f"🎤 {transcribed_text}")
                with st.chat_message("assistant"):
                    answer = process_ai_request(transcribed_text)
                    st.markdown(answer)
                    audio_file = generate_audio(answer)
                    if audio_file:
                        st.audio(audio_file, format="audio/mp3", autoplay=True)
                    st.session_state.messages.append({"role": "assistant", "content": answer, "audio_path": audio_file})
        
        if prompt := st.chat_input("أو اكتب هنا..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                answer = process_ai_request(prompt)
                st.markdown(answer)
                audio_file = generate_audio(answer)
                if audio_file:
                    st.audio(audio_file, format="audio/mp3", autoplay=True)
                st.session_state.messages.append({"role": "assistant", "content": answer, "audio_path": audio_file})
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 حالة المخزون")
        inv = get_inventory()
        for item in inv:
            # إذا كانت الكمية أقل من الحد الأدنى، نلونها بالأحمر
            if item['quantity'] <= item['min_threshold']:
                st.error(f"🔴 {item['item_name']}: {item['quantity']} (ناقص!)")
            else:
                st.success(f"🟢 {item['item_name']}: {item['quantity']}")

    with col2:
        st.subheader("🔬 أعمال المخبر")
        lab = get_lab_work()
        if lab:
            for work in lab:
                st.info(f"👤 **{work['name']}**: {work['description']} - الحالة: {work['status']}")
        else:
            st.write("لا توجد أعمال مخبر حالياً.")

with tab3:
    st.subheader("📅 مواعيد اليوم")
    # (يمكنك ربطها بدالة get_today_appointments لاحقاً)
    st.info("سيتم عرض المواعيد هنا بشكل تفصيلي.")