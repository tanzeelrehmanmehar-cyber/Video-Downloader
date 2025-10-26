# app.py
import streamlit as st
from yt_dlp import YoutubeDL
import streamlit.components.v1 as components
import time
from pathlib import Path

# ---------------- CONFIG ----------------
st.set_page_config(page_title="TechHelp Video Downloader", page_icon="🎬", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
header, footer {visibility: hidden;}
.stApp { background: linear-gradient(180deg,#020611,#041826); color: #eafcff; }
.navbar {
    background: linear-gradient(90deg, #007BFF, #00C2FF);
    padding: 10px;
    display: flex;
    justify-content: center;
    gap: 18px;
    border-radius: 0 0 12px 12px;
}
.navbar button {
    background: none;
    border: none;
    color: white;
    font-weight: 600;
    cursor: pointer;
    font-size: 16px;
}
.navbar button:hover {
    text-decoration: underline;
}
.stButton>button {
    background: linear-gradient(90deg,#00C2FF,#007BFF);
    color: white;
    border-radius: 10px;
    font-weight: 600;
}
.stButton>button:hover {
    background: linear-gradient(90deg,#007BFF,#00C2FF);
}
</style>
""", unsafe_allow_html=True)

# ---------------- NAVBAR ----------------
pages = ["Home", "AnyVideo", "Audio", "TikTok", "Instagram", "Cookie", "About"]
icons = ["🏠", "🎞️", "🎧", "🎬", "📸", "⚙️", "💡"]
cols = st.columns(len(pages))
for i, p in enumerate(pages):
    with cols[i]:
        if st.button(f"{icons[i]} {p}"):
            st.session_state["page"] = p

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

page = st.session_state["page"]

# ---------------- FUNCTIONS ----------------
def generate_download_link(url, format="video"):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
    }
    if format == "audio":
        ydl_opts["format"] = "bestaudio"
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("url"), info.get("title", "file")

def download_page(title, site_hint, format="video"):
    st.header(title)
    url = st.text_input(f"Paste {site_hint} URL below 👇")
    if st.button("🔗 Generate Download Link"):
        if not url:
            st.warning("Please enter a valid URL!")
            return
        with st.spinner("Connecting to server..."):
            time.sleep(1.2)
        try:
            dl_url, title = generate_download_link(url, format=format)
            if dl_url:
                st.balloons()
                st.success(f"✅ Download link ready for **{title}**!")
                st.markdown(f"[⬇️ Click here to download **{title}**]({dl_url})", unsafe_allow_html=True)
            else:
                st.error("❌ Failed to generate link. Try again.")
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- HOME PAGE ----------------
if page == "Home":
    home_path = Path("home.html")
    if home_path.exists():
        html_content = home_path.read_text(encoding="utf-8")
        components.html(html_content, height=700)
        st.markdown("""
        <script>
        window.addEventListener('message', (e) => {
            if (e.data && e.data.type === 'start') {
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'AnyVideo'}, '*');
            }
        });
        </script>
        """, unsafe_allow_html=True)
    else:
        st.title("🎬 TechHelp Video Downloader")
        st.info("Missing home.html — upload it next to app.py")

# ---------------- OTHER PAGES ----------------
elif page == "AnyVideo":
    download_page("🎞️ Universal Video Downloader", "any video site", "video")

elif page == "Audio":
    download_page("🎧 Audio Extractor (MP3)", "YouTube or any site", "audio")

elif page == "TikTok":
    download_page("🎬 TikTok Downloader", "TikTok", "video")

elif page == "Instagram":
    download_page("📸 Instagram Downloader", "Instagram", "video")

elif page == "Cookie":
    st.header("⚙️ Cookie Settings (Advanced)")
    st.info("If TikTok or Instagram need login, paste your cookie string here.")
    cookie_input = st.text_area("Paste cookie string")
    if st.button("💾 Save Cookie"):
        if cookie_input:
            st.session_state["cookie"] = cookie_input
            st.success("✅ Cookie saved for this session.")
        else:
            st.warning("No cookie entered.")

elif page == "About":
    st.header("💡 About TechHelp Downloader")
    st.markdown("""
    **TechHelp Downloader** is a universal online downloader built with:
    - 🐍 Python + Streamlit
    - 🎞️ yt-dlp library
    - 🌐 Chrome-based streaming links

    ⚡ Features:
    - Works in any browser (mobile or desktop)
    - Supports TikTok, Instagram, YouTube, and more
    - No files stored on our server
    - Free and fast

    💬 Created with ❤️ by TechHelp Team.
    """)
