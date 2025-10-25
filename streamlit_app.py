import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import traceback

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Universal Downloader", page_icon="🎥", layout="centered")

OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ---------------- CSS ----------------
st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#060607,#0c1016);}
h1,h2,h3 {text-align:center; color:#9ef0ff;}
.section {
  background:#0f1720; border-radius:12px; padding:20px;
  box-shadow:0 8px 25px rgba(0,0,0,0.5); margin-bottom:20px;
}
.stButton>button {
  width:100%; text-align:center;
  background:linear-gradient(90deg,#00e0ff,#0078ff);
  color:white; border:none; border-radius:10px; padding:10px 0;
  font-weight:600; margin:6px 0;
}
.stButton>button:hover {opacity:0.9;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#071018,#0f202a);}
.sidebar-btn {
  display:block; width:100%; padding:12px; margin:6px 0;
  text-align:center; border-radius:8px; font-weight:600;
  background:#0b1a27; color:#fff; border:1px solid #1c2c3a;
}
.sidebar-btn:hover {background:#13334c; cursor:pointer;}
.thumbnail {
  border-radius:10px;
  box-shadow:0 0 15px rgba(0,255,255,0.3);
  margin-top:15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- JS AUTO-CLOSE SIDEBAR ----------------
AUTO_CLOSE_JS = """
<script>
function closeSidebar(){
    const sbToggle = window.parent.document.querySelector('button[aria-label="Toggle sidebar"]');
    if (sbToggle){ sbToggle.click(); }
}
</script>
"""

# ---------------- STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"

def set_page(page_name):
    st.session_state.page = page_name
    st.markdown(AUTO_CLOSE_JS, unsafe_allow_html=True)
    st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## 🎬 Universal Downloader")
    st.markdown("---", unsafe_allow_html=True)
    if st.button("🏠 Home", on_click=set_page, args=("🏠 Home",)): pass
    if st.button("🎞️ Any Video (MP4)", on_click=set_page, args=("🎞️ Any Video (MP4)",)): pass
    if st.button("🎵 Audio (MP3)", on_click=set_page, args=("🎵 Audio (MP3)",)): pass
    if st.button("🎬 TikTok Account", on_click=set_page, args=("🎬 TikTok Account",)): pass
    if st.button("📸 Instagram Account", on_click=set_page, args=("📸 Instagram Account",)): pass
    if st.button("⚙️ Set Cookie", on_click=set_page, args=("⚙️ Set Cookie",)): pass
    if st.button("💡 About", on_click=set_page, args=("💡 About",)): pass

# ---------------- FETCH METADATA ----------------
def fetch_metadata(url):
    ydl_opts = {"quiet": True, "skip_download": True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "Unknown Title")
            uploader = info.get("uploader", "Unknown Uploader")
            duration = info.get("duration", 0)
            thumbnail = info.get("thumbnail")
            return {"title": title, "uploader": uploader, "duration": duration, "thumbnail": thumbnail}
    except Exception as e:
        st.error("❌ Unable to fetch metadata.")
        st.text(str(e))
        return None

# ---------------- DOWNLOAD ----------------
def download_with_progress(url, audio=False):
    st.write("Downloading:", url)
    outtmpl = str(OUT_DIR / "%(title).100s.%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [],
    }
    if audio:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
    else:
        ydl_opts["format"] = "best"
        ydl_opts["merge_output_format"] = "mp4"

    prog = st.progress(0)
    msg = st.empty()

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes", 0)
            if total:
                pct = int(done * 100 / total)
                prog.progress(pct)
                msg.text(f"Downloading {pct}%")
        elif d["status"] == "finished":
            prog.progress(100)
            msg.success("✅ Download complete")

    ydl_opts["progress_hooks"].append(hook)
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        st.error(str(e))
        st.error(traceback.format_exc())

# ---------------- PAGES ----------------
st.markdown("<div class='section'>", unsafe_allow_html=True)
page = st.session_state.page

if page == "🏠 Home":
    st.title("🎥 Universal Downloader (Pro)")
    st.info("Use the sidebar to choose a feature. Sidebar auto-closes when an option is selected for a clean view.")

elif page == "🎞️ Any Video (MP4)":
    st.header("🎞️ Download Any Video (MP4)")
    url = st.text_input("Paste video link here 👇")
    if url:
        meta = fetch_metadata(url)
        if meta:
            st.image(meta["thumbnail"], caption=meta["title"], use_container_width=True, output_format="auto")
            st.write(f"**Title:** {meta['title']}")
            st.write(f"**Uploader:** {meta['uploader']}")
            st.write(f"**Duration:** {meta['duration']} seconds")
        if st.button("⬇️ Download MP4"):
            download_with_progress(url)

elif page == "🎵 Audio (MP3)":
    st.header("🎵 Extract Audio (MP3)")
    url = st.text_input("Paste video link here 👇")
    if url:
        meta = fetch_metadata(url)
        if meta:
            st.image(meta["thumbnail"], caption=meta["title"], use_container_width=True)
            st.write(f"**Title:** {meta['title']}")
            st.write(f"**Uploader:** {meta['uploader']}")
        if st.button("⬇️ Download MP3"):
            download_with_progress(url, audio=True)

elif page == "🎬 TikTok Account":
    st.header("🎬 Download TikTok Account Videos")
    username = st.text_input("TikTok username (without @)")
    if username:
        if st.button("⬇️ Download All Videos"):
            download_with_progress(f"https://www.tiktok.com/@{username}")

elif page == "📸 Instagram Account":
    st.header("📸 Download Instagram Account Videos")
    username = st.text_input("Instagram username (without @)")
    if username:
        if st.button("⬇️ Download All Posts"):
            download_with_progress(f"https://www.instagram.com/{username}/")

elif page == "⚙️ Set Cookie":
    st.header("⚙️ Instagram Cookie")
    cookie = st.text_area("Paste your Instagram cookie string here:")
    if st.button("Save Cookie"):
        st.session_state["cookie"] = cookie
        st.success("Cookie saved for this session.")

elif page == "💡 About":
    st.header("💡 About App")
    st.write("Built with Streamlit + yt-dlp. Supports YouTube, TikTok, Instagram, and more.")
    st.write("Sidebar auto-closes when clicking options. Mobile friendly.")
    st.markdown("🌐 [My Projects](https://love-games.netlify.app) | [Watch Party](https://watch-party-yt.netlify.app)")

st.markdown("</div>", unsafe_allow_html=True)
