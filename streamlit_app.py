import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import base64
import traceback

# ---------------- CONFIG ----------------
APP_TITLE = "All Video Downloader"
APP_TAGLINE = "Enjoy"
st.set_page_config(page_title=f"{APP_TITLE} — {APP_TAGLINE}", page_icon="🎬", layout="wide")

OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
body, .stApp { 
    background: linear-gradient(180deg,#030407,#07101a); 
    color: #eafcff; 
    font-family: Inter, sans-serif; 
}
h1,h2,h3 { text-align:center; color:#8ef0ff; }
.card { 
    background: linear-gradient(180deg,#07121a,#08121a); 
    border-radius:14px; 
    padding:14px; 
    margin:10px; 
    box-shadow: 0 14px 46px rgba(0,0,0,0.7); 
    border:1px solid rgba(0,140,255,0.06); 
}
.stButton>button { 
    background: linear-gradient(90deg,#00c2ff,#0069ff); 
    color: white; 
    font-weight:700; 
    border-radius:10px; 
    padding:10px 18px; 
    width:100%; 
    box-shadow:0 8px 20px rgba(0,100,255,0.18); 
}
.stButton>button:hover { transform: translateY(-3px); }
input[type=text], textarea { 
    background:#07111a !important; 
    color:#eafcff !important; 
    border-radius:8px !important; 
    padding:10px !important; 
    border:1px solid #183045 !important; 
}
footer, header[data-testid="stHeader"], #MainMenu {display:none !important;}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------- CUSTOM NAVBAR ----------------
header_html = """
<div style="
    position: fixed;
    top: 0;
    width: 100%;
    z-index: 9999;
    background: linear-gradient(90deg,#00c2ff,#0069ff);
    padding: 12px 0;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 30px;
    font-weight: 700;
    color: white;
    border-radius: 0 0 12px 12px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.3);
">
    <a href="?page=Home" style="color:white;text-decoration:none;">🏠 Home</a>
    <a href="?page=AnyVideo" style="color:white;text-decoration:none;">🔎 Any Video</a>
    <a href="?page=Audio" style="color:white;text-decoration:none;">🎧 Audio</a>
    <a href="?page=TikTok" style="color:white;text-decoration:none;">🎬 TikTok</a>
    <a href="?page=Instagram" style="color:white;text-decoration:none;">📸 Instagram</a>
    <a href="?page=Cookie" style="color:white;text-decoration:none;">⚙️ Cookie</a>
    <a href="?page=About" style="color:white;text-decoration:none;">💡 About</a>
</div>
"""
st.components.v1.html(header_html, height=60, scrolling=False)
st.markdown("<div style='margin-top:80px;'></div>", unsafe_allow_html=True)

# ---------------- AUTO DOWNLOAD FUNCTION ----------------
def auto_download_button(file_path: Path, label: str = "Download"):
    """Create an auto-starting HTML download link for a given file"""
    try:
        data = file_path.read_bytes()
        b64 = base64.b64encode(data).decode()
        href = f'data:application/octet-stream;base64,{b64}'
        filename = file_path.name
        download_html = f"""
        <a id="autoDL" href="{href}" download="{filename}" style="
            display:inline-block;
            background:linear-gradient(90deg,#00c2ff,#0069ff);
            color:white;
            font-weight:700;
            padding:10px 16px;
            border-radius:8px;
            text-decoration:none;
            margin-top:10px;
        ">{label}</a>
        <script>document.getElementById('autoDL').click();</script>
        """
        st.markdown(download_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error creating download: {e}")

# ---------------- MAIN DOWNLOAD FUNCTION (with progress) ----------------
def download_video(url: str, audio_only=False):
    if not url.strip():
        st.warning("Please enter a valid URL.")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').replace('%', '')
                speed = d.get('_speed_str', '')
                eta = d.get('_eta_str', '')
                progress = float(percent) / 100
                progress_bar.progress(progress)
                status_text.markdown(
                    f"**Downloading:** {percent}% Speed: {speed} ETA: {eta}"
                )
            except Exception:
                pass
        elif d['status'] == 'finished':
            progress_bar.progress(1.0)
            status_text.markdown("✅ **Processing file... please wait**")

    ydl_opts = {
        "outtmpl": str(OUT_DIR / "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
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
        st.error(e)
        st.text(traceback.format_exc())

# ---------------- PAGE LOGIC ----------------
page = st.session_state.page
st.markdown("<div class='card'>", unsafe_allow_html=True)

if page == "Home":
    st.title("🎬 All Video Downloader")
    st.write("Welcome! Choose any platform from the top menu to start downloading.")

elif page == "AnyVideo":
    st.header("🔎 Download Any Video")
    url = st.text_input("Enter video URL")
    if st.button("Download"):
        download_video(url)

elif page == "Audio":
    st.header("🎧 Download Audio (MP3)")
    url = st.text_input("Enter video URL")
    if st.button("Download"):
        download_video(url, audio_only=True)

elif page == "TikTok":
    st.header("🎬 TikTok Video")
    url = st.text_input("Enter TikTok video URL")
    if st.button("Download"):
        download_video(url)

elif page == "Instagram":
    st.header("📸 Instagram Video")
    url = st.text_input("Enter Instagram video URL")
    if st.button("Download"):
        download_video(url)

elif page == "Cookie":
    st.header("⚙️ Cookie Settings")
    st.text_area("Paste your cookie string here", height=150)
    st.info("Add cookies here if a site requires login access.")

elif page == "About":
    st.header("💡 About")
    st.write("""
    **All Video Downloader**  
    Built with **Streamlit + yt-dlp**  
    Supports YouTube, TikTok, Instagram, and more.  
    Developer: **Tanzeel ur Rehman**
    """)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- ENTER KEY SUPPORT ----------------
enter_script = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  const inputs = document.querySelectorAll('input[type="text"]');
  inputs.forEach(inp => {
    inp.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        const btns = document.querySelectorAll('button');
        for (let b of btns) {
          if (b.innerText.toLowerCase().includes('download')) {
            b.click();
            break;
          }
        }
      }
    });
  });
});
</script>
"""
st.markdown(enter_script, unsafe_allow_html=True)
