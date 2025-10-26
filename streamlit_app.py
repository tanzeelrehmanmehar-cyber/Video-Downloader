# app.py
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import os
import platform

# ----------------------------
# ---------- Settings ----------
# ----------------------------
if platform.system() == "Linux" and os.path.exists("/storage/emulated/0"):
    DEFAULT_OUT_DIR = Path("/storage/emulated/0/TecHelp")
else:
    DEFAULT_OUT_DIR = Path.home() / "Downloads" / "TecHelp"
DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Universal Video & Audio Downloader",
    page_icon="🎬",
    layout="wide",
)

# Hide default Streamlit header/footer
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# ---------- Hamburger Menu ----------
# ----------------------------
menu_html = """
<style>
.hamburger-container {
    position: fixed; top: 15px; right: 20px; z-index: 9999;
}
.hamburger {cursor: pointer; width: 30px; height: 22px; display: flex; flex-direction: column; justify-content: space-between;}
.hamburger div {width: 100%; height: 4px; background-color: #4B3E8C; border-radius: 2px;}
.menu-items {
    display: none; position: fixed; top: 50px; right: 20px;
    background-color: white; border: 1px solid #ddd; border-radius: 8px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15); z-index: 9999; min-width: 200px;
    flex-direction: column; padding: 10px;
}
.menu-items a {text-decoration: none; color: #4B3E8C; padding: 8px; font-weight: bold; display: block;}
.menu-items a:hover {background-color: #f0f0f0; border-radius: 4px;}
.menu-active {display: flex !important; flex-direction: column;}
</style>
<div class="hamburger-container">
    <div class="hamburger" onclick="toggleMenu()"><div></div><div></div><div></div></div>
    <div id="menu" class="menu-items">
        <a href="#home">Home</a>
        <a href="#download">Download Link</a>
        <a href="#tiktok">TikTok</a>
        <a href="#instagram">Instagram</a>
    </div>
</div>
<script>
function toggleMenu() {
    var menu = document.getElementById("menu");
    menu.classList.toggle("menu-active");
}
</script>
"""
st.markdown(menu_html, unsafe_allow_html=True)

# ----------------------------
# ---------- Helper Functions ----------
# ----------------------------
def progress_hook(d, progress_bar, progress_text):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes', 0)
        if total_bytes:
            progress = min(int(downloaded_bytes / total_bytes * 100), 100)
            progress_bar.progress(progress)
            progress_text.text(f"Downloading: {d.get('filename','')}\nProgress: {progress}%")
    elif d['status'] == 'finished':
        progress_bar.progress(100)
        progress_text.text(f"Finished: {d.get('filename','')}")

def download_video(url, out_dir=DEFAULT_OUT_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    progress_text = st.empty()
    status_bar = st.progress(0)
    ydl_opts = {
        "outtmpl": str(out_dir / "%(title).100s.%(ext)s"),
        "format": "best",
        "quiet": True,
        "progress_hooks": [lambda d: progress_hook(d, status_bar, progress_text)],
        "no_warnings": True,
        "ignoreerrors": True,
        "merge_output_format": "mp4",
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        st.success(f"✅ Video saved to: {out_dir}")
    except Exception as e:
        st.error(f"⚠️ Failed: {e}")

def download_audio(url, out_dir=DEFAULT_OUT_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    progress_text = st.empty()
    status_bar = st.progress(0)
    ydl_opts = {
        "outtmpl": str(out_dir / "%(title).100s.%(ext)s"),
        "format": "bestaudio/best",
        "quiet": True,
        "progress_hooks": [lambda d: progress_hook(d, status_bar, progress_text)],
        "no_warnings": True,
        "ignoreerrors": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        st.success(f"✅ MP3 saved to: {out_dir}")
    except Exception as e:
        st.error(f"⚠️ Failed: {e}")

def get_tiktok_urls(username):
    username = username.lstrip("@")
    url = f"https://www.tiktok.com/@{username}"
    ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": True, "no_warnings": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries") if info else []
    urls = [e["url"] for e in entries if "url" in e]
    return urls

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
        "progress_hooks": [lambda d: progress_hook(d, st.progress(0), st.empty())],
    }
    profile_url = f"https://www.instagram.com/{username}/"
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([profile_url])
        st.success(f"✅ Instagram videos saved in: {out_dir}")
    except Exception as e:
        st.error(f"⚠️ Failed: {e}")

# ----------------------------
# ---------- Pages ----------
# ----------------------------
st.markdown("<h2 id='home'>🎬 Universal Video & Audio Downloader</h2>", unsafe_allow_html=True)
st.markdown("Use the hamburger menu at top-right to navigate between pages.")

# ---- Download Link Page ----
st.markdown("<h3 id='download'>Download from any link</h3>", unsafe_allow_html=True)
with st.form("link_form"):
    url_input = st.text_input("Paste video/audio link here")
    download_type = st.radio("Select type", ["Video (MP4)", "Audio (MP3)"])
    submitted = st.form_submit_button("Download")
    if submitted and url_input:
        if download_type == "Video (MP4)":
            download_video(url_input)
        else:
            download_audio(url_input)

# ---- TikTok Page ----
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h3 id='tiktok'>TikTok Account Videos</h3>", unsafe_allow_html=True)
with st.form("tiktok_form"):
    tiktok_user = st.text_input("Enter TikTok username (without @)")
    video_count = st.number_input("Number of videos (0 = all)", min_value=0, step=1)
    submitted = st.form_submit_button("Download TikTok Videos")
    if submitted and tiktok_user:
        urls = get_tiktok_urls(tiktok_user)
        if not urls:
            st.warning("⚠️ No videos found or username invalid.")
        else:
            to_download = urls if video_count == 0 else urls[:video_count]
            for u in to_download:
                download_video(u, DEFAULT_OUT_DIR / tiktok_user)

# ---- Instagram Page ----
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h3 id='instagram'>Instagram Account Videos</h3>", unsafe_allow_html=True)
st.markdown("⚠️ You must provide a valid Instagram cookie for account access.")
with st.form("insta_form"):
    ig_user = st.text_input("Enter Instagram username (without @)")
    ig_cookie = st.text_area("Paste full Instagram cookie string here")
    submitted = st.form_submit_button("Download Instagram Videos")
    if submitted and ig_user and ig_cookie:
        download_instagram_account(ig_user, ig_cookie)

st.markdown("<p style='text-align:center;color:gray'>Created with ❤️ by YourName</p>", unsafe_allow_html=True)
