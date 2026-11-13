import asyncio
import edge_tts
import tempfile
import os

async def generate_audio_async(text, voice="ar-SY-AmanyNeural"):
    # صوت "أماني" هو صوت سوري طبيعي جداً. يمكنك تغييره إلى ar-SY-LaithNeural لصوت رجالي
    communicate = edge_tts.Communicate(text, voice)
    
    # إنشاء ملف مؤقت لحفظ الصوت
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_path = temp_file.name
    temp_file.close()
    
    # توليد الصوت وحفظه
    await communicate.save(temp_path)
    return temp_path

def generate_audio(text):
    """دالة متزامنة (Sync) لسهولة استخدامها في Streamlit"""
    if not text:
        return None
    try:
        # تشغيل الدالة غير المتزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path = loop.run_until_complete(generate_audio_async(text))
        return audio_path
    except Exception as e:
        print(f"خطأ في توليد الصوت: {e}")
        return None