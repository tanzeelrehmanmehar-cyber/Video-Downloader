# app.py
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import os

# ----------------------------
# ---------- Settings ----------
# ----------------------------
DEFAULT_OUT_DIR = Path.home() / "Downloads" / "TecHelp"
DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Universal Video & Audio Downloader",
    page_icon="🎬",
    layout="wide",
)

# Hide default Streamlit header/footer
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ----------------------------
# ---------- Sidebar Menu ----------
# ----------------------------
menu = ["Home", "Download Link", "TikTok Account", "Instagram Account"]
choice = st.sidebar.selectbox("📂 Navigation", menu)

# Store Instagram cookie in session state
if "INSTAGRAM_COOKIE" not in st.session_state:
    st.session_state.INSTAGRAM_COOKIE = ""

# ----------------------------
# ---------- Helper Functions ----------
# ----------------------------
def download_video(url, out_dir=DEFAULT_OUT_DIR):
    out_dir.mkdir(exist_ok=True)
    ydl_opts = {
        "outtmpl": str(out_dir / "%(title).100s.%(ext)s"),
        "format": "best",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "merge_output_format": "mp4",
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info["entries"] if isinstance(info, dict) and "entries" in info else [info]
            for entry in entries:
                if entry and entry.get("webpage_url"):
                    ydl.download([entry["webpage_url"]])
        st.success(f"✅ Video saved to: {out_dir}")
    except Exception as e:
        st.error(f"⚠️ Failed: {e}")

def download_audio(url, out_dir=DEFAULT_OUT_DIR):
    out_dir.mkdir(exist_ok=True)
    ydl_opts = {
        "outtmpl": str(out_dir / "%(title).100s.%(ext)s"),
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info["entries"] if isinstance(info, dict) and "entries" in info else [info]
            for entry in entries:
                if entry and entry.get("webpage_url"):
                    ydl.download([entry["webpage_url"]])
        st.success(f"✅ MP3 saved to: {out_dir}")
    except Exception as e:
        st.error(f"⚠️ Failed: {e}")

def download_instagram_account(username, cookie, out_dir=DEFAULT_OUT_DIR):
    out_dir = out_dir / f"instagram_{username}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "outtmpl": str(out_dir / "%(upload_date)s_%(id)s.%(ext)s"),
        "format": "best",
        "quiet": False,
        "no_warnings": True,
        "ignoreerrors": True,
        "merge_output_format": "mp4",
        "cookiesfromstring": True,
        "cookiefile": cookie,
    }
    profile_url = f"https://www.instagram.com/{username}/"
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([profile_url])
        st.success(f"✅ Instagram videos saved in: {out_dir}")
    except Exception as e:
        st.error(f"⚠️ Failed to download Instagram account @{username}: {e}")

# ----------------------------
# ---------- Pages ----------
# ----------------------------
if choice == "Home":
    st.markdown("<h2 style='text-align:center'>🎬 Universal Video & Audio Downloader</h2>", unsafe_allow_html=True)
    st.markdown("Use the sidebar to navigate between features.")

elif choice == "Download Link":
    st.markdown("### Download from any link (Video/Audio)")
    with st.form("link_form"):
        url_input = st.text_input("Paste video/audio link here")
        download_type = st.radio("Select type", ["Video (MP4)", "Audio (MP3)"])
        submitted = st.form_submit_button("Download")
        if submitted and url_input:
            if download_type == "Video (MP4)":
                download_video(url_input)
            else:
                download_audio(url_input)

elif choice == "TikTok Account":
    st.markdown("### Download TikTok Account Videos")
    with st.form("tiktok_form"):
        tiktok_user = st.text_input("Enter TikTok username (without @)")
        video_count = st.number_input("Number of videos (0 = all)", min_value=0, step=1)
        submitted = st.form_submit_button("Download TikTok Videos")
        if submitted and tiktok_user:
            from yt_dlp import YoutubeDL
            def get_tiktok_urls(username):
                username = username.lstrip("@")
                url = f"https://www.tiktok.com/@{username}"
                ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": True, "no_warnings": True}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                entries = info.get("entries") if info else []
                urls = [e["url"] for e in entries if "url" in e]
                return urls
            urls = get_tiktok_urls(tiktok_user)
            if not urls:
                st.warning("⚠️ No videos found or username invalid.")
            else:
                to_download = urls if video_count == 0 else urls[:video_count]
                for u in to_download:
                    download_video(u, DEFAULT_OUT_DIR / tiktok_user)

elif choice == "Instagram Account":
    st.markdown("### Download Instagram Account Videos")
    st.markdown("⚠️ You must provide a valid Instagram cookie for account access.")
    with st.form("insta_form"):
        ig_user = st.text_input("Enter Instagram username (without @)")
        ig_cookie = st.text_area("Paste full Instagram cookie string here")
        submitted = st.form_submit_button("Download Instagram Videos")
        if submitted and ig_user and ig_cookie:
            st.session_state.INSTAGRAM_COOKIE = ig_cookie
            download_instagram_account(ig_user, st.session_state.INSTAGRAM_COOKIE)

st.markdown("<p style='text-align:center;color:gray'>Created with ❤️ by YourName</p>", unsafe_allow_html=True)
