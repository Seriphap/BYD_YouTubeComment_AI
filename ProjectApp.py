import streamlit as st
import pandas as pd
import requests
import io
from comment_fetcher import get_all_comments
from google import genai

# โหลด API key จาก .streamlit/secrets.toml
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# สร้าง client Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# รายชื่อ YouTube video ID ที่ต้องการดึงความคิดเห็น
video_ids = ["OMV9F9zB4KU", "87lJCDADWCo", "CbkX7H-0BIU"]

st.header("🤖 Analysis of BYD YouTube Comment Using Gemini-2.0-Flash")

#display video
st.subheader("▶️ Video Reference 🔴")

# แบ่ง layout เป็น 3 column
col1, col2, col3 = st.columns(3)

with col1:
    st.video(f"https://www.youtube.com/watch?v={video_ids[0]}")
    st.caption("video 1")

with col2:
    st.video(f"https://www.youtube.com/watch?v={video_ids[1]}")
    st.caption("video 2")

with col3:
    st.video(f"https://www.youtube.com/watch?v={video_ids[2]}")
    st.caption("vidio 3")

with st.sidebar:
    st.subheader("📜 Conversations History ")

    if st.session_state.get("qa_history"):
        for i, item in enumerate(reversed(st.session_state.qa_history[-5:]), 1):
            st.markdown(f"**{i}. คำถาม:** {item['question']}")
            st.markdown(f"✍️ คำตอบ: {item['answer'][:150]}...")
            st.markdown("---")

        if st.button("🗑️ Clear Conversations History"):
            st.session_state.qa_history = []
    else:
        st.info("No Conversations History")

# ตัวเลือก input
option = st.radio("เลือกแหล่งข้อมูลความคิดเห็น", [
    "📁 Access Stored Data from Jun 04, 2025",
    "🔄 Retrieve the Latest YouTube Comments"
])

df = None

# --- 1. โหลดจาก Google Drive CSV ---
if option == "📁 Access Stored Data from Jun 04, 2025":
    file_id = "1anFtZ68jj6GQ5NijicTaJkxxiMo66vUx"
    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

    try:
        st.info("🔄 Loading...")
        response = requests.get(download_url)
        response.raise_for_status()
        df = pd.read_csv(io.BytesIO(response.content))
        st.success(f"✅ Done: {len(df)} Comments")
    except Exception as e:
        st.error(f"❌ File can not download: {e}")
        st.stop()

# --- 2. ดึงความคิดเห็นใหม่จาก YouTube ---
elif option == "🔄 Retrieve the Latest YouTube Comments":
    if st.button("📥 Loading..."):
        with st.spinner("⏳ Loading comment from YouTube..."):
            df = get_all_comments(video_ids, YOUTUBE_API_KEY)
            df.to_csv("youtube_comments.csv", index=False)
            st.success(f"✅ Done: {len(df)} Comments")
    else:
        st.warning("👆 please click the botton to retrieve the comments")
        st.stop()

# --- วิเคราะห์ด้วย Gemini ---
if df is not None and not df.empty:
    st.subheader("🤖 Ask AI")
    
    # แนะนำคำถามแบบกดปุ่ม
    #------------
    st.markdown("💡 **Suggested Questions**")
    suggestions = {
        "📈 ผู้ชมรู้สึกอย่างไร? (Sentiment)": "วิเคราะห์ว่าโดยรวมผู้ชมรู้สึกอย่างไรกับวิดีโอนี้ (positive / negative / neutral) พร้อมยกตัวอย่างข้อความสนับสนุน",
        "💬 คนพูดถึงอะไรบ่อยที่สุด?": "จากความคิดเห็นทั้งหมด ผู้ชมพูดถึงประเด็นใดบ่อยที่สุดในเชิงบวกหรือลบ",
        "🎯 ข้อเสนอแนะ / คำวิจารณ์": "สรุปข้อเสนอแนะหรือคำวิจารณ์จากผู้ชมเกี่ยวกับวิดีโอนี้",
    }
    if "selected_prompt" not in st.session_state:
        st.session_state.selected_prompt = ""

    cols = st.columns(len(suggestions))
    for i, (label, prompt_text) in enumerate(suggestions.items()):
        if cols[i].button(label):
            st.session_state.selected_prompt = prompt_text

    #------------
    # กล่องป้อนคำถาม
    question = st.text_area(
    "💬 Your Question",
    value=st.session_state.selected_prompt,
    placeholder="Example: What are people saying about BYD ?"
    )
    
    #------
    if st.button("🚀 วิเคราะห์ด้วย Gemini AI"):
        if df is not None and question:
            with st.spinner("🔍 AI กำลังวิเคราะห์..."):
                comments_text = "\n".join(df["comment"].astype(str).tolist())[:30000]

                prompt = f"""
                ความคิดเห็นจากผู้ชม YouTube:
                {comments_text}

                คำถาม:
                {question}
                """

                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt.strip()
                    )

                    answer = response.text
                    st.success("✅ วิเคราะห์สำเร็จ")
                    st.subheader("📊 คำตอบจาก Gemini:")
                    st.write(answer)

                    # ✅ เก็บใน history
                    if "qa_history" not in st.session_state:
                        st.session_state.qa_history = []

                    st.session_state.qa_history.append({
                        "question": question,
                        "answer": answer
                    })
                    
                    st.session_state.selected_prompt = ""  # เคลียร์ prompt suggestion หลังวิเคราะห์

                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาดจาก Gemini: {e}")

        #------
   

