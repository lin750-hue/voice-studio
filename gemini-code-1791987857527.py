import streamlit as st
import asyncio
import subprocess
import edge_tts
import os

# إعدادات الصفحة والتصميم السينمائي
st.set_page_config(page_title="استوديو الصوت السينمائي", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .neon-header {
        text-align: center; color: #00e5ff; font-size: 28px; font-weight: bold;
        text-shadow: 0 0 15px rgba(0,229,255,0.5); padding: 15px;
        background: #131b2e; border-radius: 12px; border: 1px solid #1e293b; margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%; background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
        color: white; font-size: 18px; font-weight: bold; padding: 12px;
        border-radius: 10px; border: none; box-shadow: 0 0 15px rgba(0, 198, 255, 0.4);
    }
    .stButton>button:hover { transform: scale(1.01); color: #fff; }
</style>
<div class="neon-header">🎙️ صانع الصوت السينمائي الاحترافي (شغال 24 ساعة مجاناً)</div>
""", unsafe_allow_html=True)

# 1. مكتبة اللهجات واللكنات (عربي + إنجليزي)
VOICE_LIBRARY = {
    "مصر - راوي وثائقي رخيم (شاكر)": "ar-EG-ShakirNeural",
    "مصر - صوت نسائي واضح (سلمى)": "ar-EG-SalmaNeural",
    "السعودية - راوي فخم (حامد)": "ar-SA-HamedNeural",
    "السعودية - صوت نسائي (زارية)": "ar-SA-ZariyahNeural",
    "الإمارات - صوت رجالي (حمد)": "ar-AE-HamdanNeural",
    "الإمارات - صوت نسائي (فاطمة)": "ar-AE-FatimaNeural",
    "الكويت - صوت رجالي (فهد)": "ar-KW-FahedNeural",
    "قطر - صوت رجالي (معاذ)": "ar-QA-MoazNeural",
    "سوريا - صوت رجالي شامي (ليث)": "ar-SY-LaithNeural",
    "سوريا - صوت نسائي شامي (أمل)": "ar-SY-AmanyNeural",
    "لبنان - صوت رجالي (رامي)": "ar-LB-RamiNeural",
    "لبنان - صوت نسائي (ليلى)": "ar-LB-LaylaNeural",
    "الأردن - صوت رجالي (تيم)": "ar-JO-TaimNeural",
    "الأردن - صوت نسائي (سناء)": "ar-JO-SanaNeural",
    "العراق - صوت رجالي (باسل)": "ar-IQ-BasselNeural",
    "العراق - صوت نسائي (رنا)": "ar-IQ-RanaNeural",
    "المغرب - صوت رجالي (جمال)": "ar-MA-JamalNeural",
    "المغرب - صوت نسائي (منى)": "ar-MA-MounaNeural",
    "تونس - صوت رجالي (هادي)": "ar-TN-HediNeural",
    "الجزائر - صوت رجالي (إسماعيل)": "ar-DZ-IsmaelNeural",
    "الجزائر - صوت نسائي (أمينة)": "ar-DZ-AminaNeural",
    "إنجليزي (أمريكي) - راوي وثائقي عميق (Christopher)": "en-US-ChristopherNeural",
    "إنجليزي (أمريكي) - راوي سينمائي فخم (Eric)": "en-US-EricNeural",
    "إنجليزي (أمريكي) - راوي يوتيوب حديث (Andrew)": "en-US-AndrewNeural",
    "إنجليزي (أمريكي) - راوي دافئ (Brian)": "en-US-BrianNeural",
    "إنجليزي (أمريكي) - صوت نسائي احترافي (Ava)": "en-US-AvaNeural",
    "إنجليزي (أمريكي) - صوت طفلة (Ana - Child)": "en-US-AnaNeural",
    "إنجليزي (بريطاني) - راوي BBC كلاسيكي (Ryan)": "en-GB-RyanNeural",
    "إنجليزي (بريطاني) - صوت نسائي راقي (Sonia)": "en-GB-SoniaNeural",
    "إنجليزي (بريطاني) - صوت طفلة (Maisie - Child)": "en-GB-MaisieNeural",
    "إنجليزي (أسترالي) - راوي طبيعة ومغامرات (William)": "en-AU-WilliamNeural",
    "إنجليزي (أيرلندي) - حكواتي درامي (Connor)": "en-IE-ConnorNeural",
}

# 2. محولات الأعمار والنبرات
AGE_PRESETS = {
    "السن الطبيعي للصوت (Natural Adult)": {"pitch": "+0Hz", "ffmpeg_pitch": 1.0},
    "كبير في السن / حكيم عميق (Elderly / Wise Narrator)": {"pitch": "-12Hz", "ffmpeg_pitch": 0.88},
    "راوي رعب وأعماق سحيقة (Deep Horror / Abyss)": {"pitch": "-20Hz", "ffmpeg_pitch": 0.80},
    "شاب حيوي (Energetic Youth)": {"pitch": "+8Hz", "ffmpeg_pitch": 1.07},
    "طفل صغير (Young Child)": {"pitch": "+25Hz", "ffmpeg_pitch": 1.25},
}

async def generate_raw_voice(text, voice_id, pitch_str, output_path):
    communicate = edge_tts.Communicate(text, voice_id, pitch=pitch_str)
    await communicate.save(output_path)

# تقسيم الشاشة لعمودين
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. إعدادات الصوت والراوي")
    selected_voice = st.selectbox("اللغة واللكنة وصوت الراوي:", list(VOICE_LIBRARY.keys()))
    selected_age = st.selectbox("الفئة العمرية وطابع الصوت:", list(AGE_PRESETS.keys()))
    speed = st.slider("سرعة الإلقاء (Speed Control):", min_value=0.6, max_value=1.4, value=1.0, step=0.05)

    st.subheader("2. الفلاتر والمعالجة السينمائية")
    bass_boost = st.checkbox("تضخيم وبث الصوت السينمائي (Rich Bass Boost)", value=True)
    dramatic_pause = st.checkbox("إضافة صمت درامي بين الجمل (Dramatic Pauses)", value=True)
    studio_clean = st.checkbox("تنقية وعزل الترددات المزعجة (Studio EQ Filter)", value=True)

with col2:
    st.subheader("3. السكريبت والتوليد")
    script_text = st.text_area(
        "اكتبي السكريبت هنا (ضعي ... لأخذ نفس أو وقفة درامية):",
        value="...وكانت هذه المياه المظلمة تسمى بالمقبرة، حيث لا يجرؤ أحد على الغوص فيها... أسرار الأعماق لم تبح بكل شيء بعد.",
        height=200
    )

    if st.button("🎙️ توليد الصوت السينمائي الآن"):
        if not script_text.strip():
            st.error("يرجى كتابة السكريبت أولاً!")
        else:
            with st.spinner("جاري توليد الصوت وتطبيق الفلاتر السينمائية..."):
                processed_text = script_text
                if dramatic_pause:
                    processed_text = processed_text.replace("...", " ... ، ... ").replace("\n", " ... \n ")

                raw_file = "raw_voice.mp3"
                final_file = "cinematic_master.mp3"

                voice_id = VOICE_LIBRARY[selected_voice]
                pitch_str = AGE_PRESETS[selected_age]["pitch"]

                # توليد الصوت الأساسي
                asyncio.run(generate_raw_voice(processed_text, voice_id, pitch_str, raw_file))

                # بناء فلاتر FFmpeg الصوتية
                filters = []
                pitch_factor = AGE_PRESETS[selected_age]["ffmpeg_pitch"]

                if pitch_factor != 1.0:
                    filters.append(f"asetrate=44100*{pitch_factor},aresample=44100,atempo={1/pitch_factor:.3f}")
                if speed != 1.0:
                    filters.append(f"atempo={speed}")
                if studio_clean:
                    filters.append("highpass=f=75,lowpass=f=14000")
                if bass_boost:
                    filters.append("bass=g=7:f=110:w=0.6,treble=g=2:f=8000,acompressor=threshold=-18dB:ratio=3")

                filter_chain = ",".join(filters) if filters else "anull"

                cmd = ["ffmpeg", "-y", "-i", raw_file, "-af", filter_chain, "-b:a", "192k", final_file]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                st.success("✅ تم توليد ومعالجة الصوت بنجاح!")
                
                with open(final_file, "rb") as audio_bytes:
                    audio_data = audio_bytes.read()
                    st.audio(audio_data, format="audio/mp3")
                    st.download_button(
                        label="⬇️ تحميل ملف الصوت (MP3)",
                        data=audio_data,
                        file_name="cinematic_voiceover.mp3",
                        mime="audio/mp3"
                    )