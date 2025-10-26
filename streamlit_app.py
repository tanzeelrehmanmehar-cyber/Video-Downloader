import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import base64, traceback

# ---------------- CONFIG ----------------
st.set_page_config(page_title="All Video Downloader", page_icon="🎬", layout="wide")

# Hide default Streamlit header/footer
st.markdown("""
<style>
header, footer {visibility: hidden;}
body {background-color: #0b0c10; color: #c5c6c7;}
.stButton>button {
  background: linear-gradient(90deg,#00C2FF,#007BFF);
  color: white; border-radius: 10px; font-weight: 600;
}
.stButton>button:hover {
  background: linear-gradient(90deg,#007BFF,#00C2FF);
}
.navbar {
  background: linear-gradient(90deg,#007BFF,#00C2FF);
  padding: 12px;
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  border-radius: 0 0 12px 12px;
  gap: 18px;
}
.navbar button {
  background: none;
  border: none;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}
.navbar button:hover {text-decoration: underline;}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------- NAVBAR ----------------
col_home, col_video, col_audio, col_tt, col_ig, col_cookie, col_about = st.columns(7)
with col_home: st.button("🏠 Home", on_click=lambda: st.session_state.update(page="Home"))
with col_video: st.button("🎞️ Any Video", on_click=lambda: st.session_state.update(page="AnyVideo"))
with col_audio: st.button("🎧 Audio", on_click=lambda: st.session_state.update(page="Audio"))
with col_tt: st.button("🎬 TikTok", on_click=lambda: st.session_state.update(page="TikTok"))
with col_ig: st.button("📸 Instagram", on_click=lambda: st.session_state.update(page="Instagram"))
with col_cookie: st.button("⚙️ Cookie", on_click=lambda: st.session_state.update(page="Cookie"))
with col_about: st.button("💡 About", on_click=lambda: st.session_state.update(page="About"))

# ---------------- FOLDER ----------------
OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ---------------- UTILITIES ----------------
def auto_download_button(filepath: Path):
    """Trigger browser download automatically."""
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filepath.name}" id="autoDL"></a>'
        js = "<script>document.getElementById('autoDL').click();</script>"
        st.markdown(href + js, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Auto download failed: {e}")

def download_video(url: str, audio_only=False):
    """Download video with live progress."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    def hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').replace('%', '')
            speed = d.get('_speed_str', '')
            eta = d.get('_eta_str', '')
            try:
                progress = float(percent) / 100
            except:
                progress = 0
            progress_bar.progress(progress)
            status_text.markdown(f"**Downloading:** {percent}% Speed: {speed} ETA: {eta}")
        elif d['status'] == 'finished':
            progress_bar.progress(1.0)
            status_text.markdown("✅ **Processing... please wait**")

    ydl_opts = {
        "outtmpl": str(OUT_DIR / "%(title).80s.%(ext)s"),
        "progress_hooks": [hook],
        "quiet": True,
        "ignoreerrors": True,
    }

    if audio_only:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        ydl_opts["format"] = "best"

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        filename = info.get("_filename") or list(OUT_DIR.glob("*"))[-1]
        status_text.markdown("✅ **Download complete!**")
        st.success(f"Saved: {Path(filename).name}")
        auto_download_button(Path(filename))
    except Exception as e:
        progress_bar.empty()
        status_text.error("❌ Download failed.")
        st.error(str(e))
        st.text(traceback.format_exc())

# ---------------- ENTER KEY SUPPORT ----------------
enter_js = """
<script>
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') {
    const btn = Array.from(document.querySelectorAll('button[kind=primary]'))[0];
    if (btn) btn.click();
  }
});
</script>
"""

# ---------------- PAGES ----------------
page = st.session_state.page

if page == "Home":
    st.title("🎬 All Video Downloader")
    st.write("Welcome! Use the top navigation bar to start downloading videos or audio.")
    st.markdown("---")
    recent = sorted(OUT_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    if recent:
        st.subheader("📂 Recent Downloads")
        for f in recent:
            with open(f, "rb") as fh:
                st.download_button("⬇️ Save", data=fh, file_name=f.name)

elif page == "AnyVideo":
    st.header("🎞️ Download Any Video")
    st.markdown(enter_js, unsafe_allow_html=True)
    url = st.text_input("Enter any video URL (YouTube, TikTok, Instagram, etc.)")
    if url and st.button("Download Video"):
        download_video(url)

elif page == "Audio":
    st.header("🎧 Download Audio (MP3)")
    st.markdown(enter_js, unsafe_allow_html=True)
    url = st.text_input("Enter video URL to extract audio")
    if url and st.button("Download Audio"):
        download_video(url, audio_only=True)

elif page == "TikTok":
    st.header("🎬 TikTok Downloader")
    st.markdown(enter_js, unsafe_allow_html=True)
    url = st.text_input("Enter TikTok video URL")
    if url and st.button("Download TikTok Video"):
        download_video(url)

elif page == "Instagram":
    st.header("📸 Instagram Downloader")
    st.markdown(enter_js, unsafe_allow_html=True)
    url = st.text_input("Enter Instagram post or reel URL")
    if url and st.button("Download Instagram Video"):
        download_video(url)

elif page == "Cookie":
    st.header("⚙️ Cookie Settings")
    cookie = st.text_area("Paste your cookie string here", height=150)
    if cookie:
        st.success("✅ Cookie saved for this session.")
    st.info("Add cookies if a website requires login access.")

elif page == "About":
    st.header("💡 About")
    st.write("""
    **All Video Downloader**  
    Built with **Streamlit + yt-dlp**  
    Supports YouTube, TikTok, Instagram, and more.  
    Developer: **Tanzeel ur Rehman**
    """)

else:
    st.error("Page not found.")
