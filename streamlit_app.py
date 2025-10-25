import os
import streamlit as st
from yt_dlp import YoutubeDL

# ---------------------- Page Setup ----------------------
st.set_page_config(page_title="🎬 Universal Downloader", layout="centered")

OUT_DIR = "downloads"
os.makedirs(OUT_DIR, exist_ok=True)

st.markdown("""
<style>
body { background-color: #0e1117; color: #fafafa; }
h1, h2, h3, h4, h5, h6, .stRadio label { color: #fafafa !important; }
.stButton>button {
    background-color: #0e76a8; color: white; border-radius: 8px; padding: 0.5em 1em;
}
.stButton>button:hover {
    background-color: #0984e3;
}
.stTextInput>div>div>input, .stTextArea>div>textarea {
    background-color: #1c1f26; color: #fafafa; border: 1px solid #333;
}
</style>
""", unsafe_allow_html=True)

st.title("🎬 Universal Downloader")
st.caption("Download videos and music from TikTok, YouTube, Instagram & more — right from your browser.")

# ---------------------- Sidebar Menu ----------------------
menu = st.sidebar.radio(
    "📂 Select Option",
    [
        "🏠 Home",
        "🎞️ Download from Custom Link (MP4)",
        "🎵 Download Audio Only (MP3)",
        "🎥 Download TikTok Account Videos",
        "📸 Download Instagram Account Videos",
        "⚙️ Set Instagram Cookie",
        "🌐 Explore My Projects"
    ]
)

INSTAGRAM_COOKIE = st.session_state.get("INSTAGRAM_COOKIE", "")


# ---------------------- Core Download Helper ----------------------
def download_media(url, audio_only=False, cookie=None):
    if not url:
        st.warning("⚠️ Please enter a valid link.")
        return

    progress = st.progress(0)
    st.info("⏳ Preparing your download...")

    try:
        if audio_only:
            ydl_opts = {
                "outtmpl": os.path.join(OUT_DIR, "%(title).100s.%(ext)s"),
                "format": "bestaudio/best",
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        else:
            ydl_opts = {
                "outtmpl": os.path.join(OUT_DIR, "%(title).100s.%(ext)s"),
                "format": "best",
                "quiet": True,
                "merge_output_format": "mp4",
            }

        if cookie:
            cookie_file = "cookie.txt"
            with open(cookie_file, "w") as f:
                f.write(cookie)
            ydl_opts["cookiefile"] = cookie_file

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        progress.progress(100)
        st.success("✅ Download completed successfully!")

        with open(filename, "rb") as f:
            st.download_button(
                label="⬇️ Download File",
                data=f,
                file_name=os.path.basename(filename),
                mime="audio/mpeg" if audio_only else "video/mp4",
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")


# ---------------------- TikTok Downloader ----------------------
def download_tiktok_account(username):
    if not username:
        st.warning("⚠️ Enter a valid TikTok username.")
        return

    username = username.lstrip("@")
    playlist_url = f"https://www.tiktok.com/@{username}"
    st.info(f"🎬 Fetching TikTok videos for @{username} ...")

    try:
        ydl_opts = {
            "outtmpl": os.path.join(OUT_DIR, f"{username}_%(id)s.%(ext)s"),
            "format": "best",
            "quiet": True,
            "merge_output_format": "mp4",
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])

        st.success(f"✅ All available videos from @{username} downloaded.")
    except Exception as e:
        st.error(f"❌ Failed: {e}")


# ---------------------- Instagram Downloader ----------------------
def download_instagram_account(username, cookie):
    if not username:
        st.warning("⚠️ Enter a valid Instagram username.")
        return
    if not cookie:
        st.warning("⚠️ Please set your Instagram cookie first.")
        return

    username = username.lstrip("@")
    profile_url = f"https://www.instagram.com/{username}/"

    cookie_file = "ig_cookie.txt"
    with open(cookie_file, "w") as f:
        f.write(cookie)

    st.info(f"📸 Downloading all videos from @{username} ...")
    try:
        ydl_opts = {
            "outtmpl": os.path.join(OUT_DIR, f"instagram_{username}_%(id)s.%(ext)s"),
            "format": "best",
            "quiet": True,
            "merge_output_format": "mp4",
            "cookiefile": cookie_file,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([profile_url])

        st.success(f"✅ Done! All videos from @{username} saved in '{OUT_DIR}' folder.")
    except Exception as e:
        st.error(f"❌ Failed: {e}")


# ---------------------- Pages ----------------------
if menu == "🏠 Home":
    st.markdown("""
    ### 👋 Welcome!
    Your **Universal Downloader** for everything:
    - 🎞️ Download any video (MP4)
    - 🎵 Extract MP3 audio
    - 🎥 TikTok full profile video downloads
    - 📸 Instagram account downloader (with cookie)
    ---
    **Tip:** Paste valid links and click download — your files will appear instantly below.
    """)

elif menu == "🎞️ Download from Custom Link (MP4)":
    url = st.text_input("🎥 Paste any video link:")
    if st.button("Download Video"):
        download_media(url, audio_only=False)

elif menu == "🎵 Download Audio Only (MP3)":
    url = st.text_input("🎧 Paste any video or music link:")
    if st.button("Download Audio"):
        download_media(url, audio_only=True)

elif menu == "🎥 Download TikTok Account Videos":
    username = st.text_input("Enter TikTok username (without @):")
    if st.button("Download TikTok Videos"):
        download_tiktok_account(username)

elif menu == "📸 Download Instagram Account Videos":
    username = st.text_input("Enter Instagram username (without @):")
    if st.button("Download Instagram Videos"):
        download_instagram_account(username, INSTAGRAM_COOKIE)

elif menu == "⚙️ Set Instagram Cookie":
    cookie = st.text_area("Paste your full Instagram cookie string here:")
    if st.button("Save Cookie"):
        st.session_state["INSTAGRAM_COOKIE"] = cookie
        st.success("✅ Cookie saved successfully (session-based).")

elif menu == "🌐 Explore My Projects":
    st.markdown("""
    - 💖 [Love Games](https://love-games.netlify.app)
    - 🎬 [Watch Party](https://watch-party-yt.netlify.app)
    - 🧠 Made by: **Tanzeel ur Rehman**
    """)
