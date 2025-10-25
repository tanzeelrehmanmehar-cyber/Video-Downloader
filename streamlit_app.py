import os
import streamlit as st
from yt_dlp import YoutubeDL

# ---------------------- SETUP ----------------------
st.set_page_config(
    page_title="🎬 All-in-One Downloader",
    layout="centered",
    page_icon="🎥",
)

OUT_DIR = "downloads"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------- STYLES ----------------------
st.markdown("""
    <style>
    body { background-color: #0e1117; color: white; }
    .stTextInput > div > div > input { background-color: #1c1f26; color: white; }
    .stTextArea textarea { background-color: #1c1f26; color: white; }
    .css-1d391kg { background-color: #0e1117; }
    .stButton>button {
        background-color: #00c853;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6em 1.5em;
    }
    .stButton>button:hover { background-color: #00e676; }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 All-in-One Downloader")
st.caption("Download from TikTok, YouTube, Instagram & more in one place!")

# ---------------------- SIDEBAR MENU ----------------------
menu = st.sidebar.radio(
    "📂 Choose an Option:",
    [
        "🏠 Home",
        "🎞️ Download Any Video (MP4)",
        "🎵 Download Audio (MP3)",
        "🎬 TikTok Account Downloader",
        "📸 Instagram Account Downloader",
        "⚙️ Set Instagram Cookie",
        "💡 About / Projects"
    ]
)

INSTAGRAM_COOKIE = st.session_state.get("INSTAGRAM_COOKIE", "")

# ---------------------- HELPER FUNCTIONS ----------------------
def download_media(url, audio_only=False, cookie=None):
    """Generic media downloader"""
    if not url:
        st.warning("⚠️ Please paste a valid link first.")
        return

    st.info("⏳ Downloading... Please wait...")
    try:
        opts = {
            "outtmpl": os.path.join(OUT_DIR, "%(title).100s.%(ext)s"),
            "quiet": True,
            "merge_output_format": "mp4",
        }

        if audio_only:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            opts["format"] = "best"

        if cookie:
            cookie_file = "cookie.txt"
            with open(cookie_file, "w") as f:
                f.write(cookie)
            opts["cookiefile"] = cookie_file

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        st.success("✅ Download complete!")
        with open(filename, "rb") as f:
            st.download_button(
                label="⬇️ Click to Download",
                data=f,
                file_name=os.path.basename(filename),
                mime="audio/mpeg" if audio_only else "video/mp4",
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")


def download_tiktok_account(username):
    """Download all videos from TikTok account"""
    if not username:
        st.warning("⚠️ Please enter a TikTok username.")
        return

    username = username.lstrip("@")
    playlist_url = f"https://www.tiktok.com/@{username}"
    st.info(f"📥 Fetching all videos from @{username}...")

    try:
        ydl_opts = {
            "outtmpl": os.path.join(OUT_DIR, f"tiktok_{username}_%(id)s.%(ext)s"),
            "format": "best",
            "quiet": True,
            "merge_output_format": "mp4",
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])

        st.success(f"✅ Downloaded all available videos from @{username}.")

    except Exception as e:
        st.error(f"❌ Failed: {e}")


def download_instagram_account(username, cookie):
    """Download all videos from Instagram account"""
    if not username:
        st.warning("⚠️ Please enter Instagram username.")
        return
    if not cookie:
        st.warning("⚠️ Please set Instagram cookie first (in '⚙️ Set Cookie').")
        return

    username = username.lstrip("@")
    profile_url = f"https://www.instagram.com/{username}/"

    cookie_file = "ig_cookie.txt"
    with open(cookie_file, "w") as f:
        f.write(cookie)

    st.info(f"📥 Downloading videos from @{username}...")

    try:
        ydl_opts = {
            "outtmpl": os.path.join(OUT_DIR, f"instagram_{username}_%(id)s.%(ext)s"),
            "format": "best",
            "quiet": True,
            "merge_output_format": "mp4",
            "ignoreerrors": True,
            "cookiefile": cookie_file,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([profile_url])

        st.success(f"✅ All available videos from @{username} downloaded!")

    except Exception as e:
        st.error(f"❌ Error: {e}")


# ---------------------- PAGE HANDLERS ----------------------
if menu == "🏠 Home":
    st.markdown("""
    ### 👋 Welcome to All-in-One Downloader
    This app lets you:
    - 🎞️ Download any video (TikTok, YouTube, etc.)
    - 🎵 Convert to MP3 (audio only)
    - 📸 Download all posts from TikTok or Instagram profiles
    - ⚙️ Manage cookies for login-required sites

    ---
    💾 All downloads are saved in `downloads/` folder.
    """)

elif menu == "🎞️ Download Any Video (MP4)":
    url = st.text_input("🎥 Paste video link:")
    if st.button("Download Video"):
        download_media(url, audio_only=False)

elif menu == "🎵 Download Audio (MP3)":
    url = st.text_input("🎧 Paste video link to extract audio:")
    if st.button("Download Audio"):
        download_media(url, audio_only=True)

elif menu == "🎬 TikTok Account Downloader":
    username = st.text_input("Enter TikTok username (without @):")
    if st.button("Download TikTok Videos"):
        download_tiktok_account(username)

elif menu == "📸 Instagram Account Downloader":
    username = st.text_input("Enter Instagram username (without @):")
    if st.button("Download Instagram Videos"):
        download_instagram_account(username, INSTAGRAM_COOKIE)

elif menu == "⚙️ Set Instagram Cookie":
    cookie = st.text_area("Paste your Instagram cookie string below:")
    if st.button("Save Cookie"):
        st.session_state["INSTAGRAM_COOKIE"] = cookie
        st.success("✅ Cookie saved successfully! You can now download Instagram videos.")

elif menu == "💡 About / Projects":
    st.markdown("""
    ### 🌍 My Projects
    - 💖 [Love Games](https://love-games.netlify.app)
    - 🎬 [Watch Party](https://watch-party-yt.netlify.app)
    
    ---
    🧠 Created with Streamlit + yt-dlp  
    💾 Fully works on Streamlit Cloud or local PC
    """)
