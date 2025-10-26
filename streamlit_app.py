# app.py
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import threading
import time
import shutil
import tempfile
import traceback
import streamlit.components.v1 as components
from typing import List, Optional
import os

# --------- App branding ----------
APP_TITLE = "All Video Downloader"
APP_TAGLINE = "Enjoy"
HOME_HTML = "home.html"  # must be in same folder

# --------- Page config ----------
st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_TAGLINE}",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------- Folders ----------
OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# --------- CSS (dark - neon) ----------
st.markdown(
    """
<style>
/* App theme */
body, .stApp { background: linear-gradient(180deg,#030407,#07101a); color: #eafcff; font-family: Inter, sans-serif; }
h1,h2,h3 { text-align:center; color:#8ef0ff; }

/* Card */
.card { background: linear-gradient(180deg,#07121a,#08121a); border-radius:14px; padding:14px; margin:10px; box-shadow: 0 14px 46px rgba(0,0,0,0.7); border:1px solid rgba(0,140,255,0.06); }

/* Buttons */
.stButton>button { background: linear-gradient(90deg,#00c2ff,#0069ff); color: white; font-weight:700; border-radius:10px; padding:10px 18px; width:100%; box-shadow:0 8px 20px rgba(0,100,255,0.18); }
.stButton>button:hover { transform: translateY(-3px); }

/* Inputs */
input[type=text], textarea { background:#07111a !important; color:#eafcff !important; border-radius:8px !important; padding:10px !important; border:1px solid #183045 !important; }

/* Grid */
.grid { display:flex; flex-wrap:wrap; gap:14px; justify-content:center; margin-top:12px; }
.grid-item { width:300px; background: linear-gradient(180deg,#08121a,#0b1720); border-radius:12px; padding:8px; box-shadow:0 10px 30px rgba(0,0,0,0.6); transition: transform .18s ease, box-shadow .18s ease; border:1px solid rgba(0,120,255,0.04); }
.grid-item:hover { transform: translateY(-6px); box-shadow: 0 18px 40px rgba(0,140,255,0.12); }
.grid-thumb { width:100%; height:170px; object-fit:cover; border-radius:8px; transition: transform .22s ease, box-shadow .22s ease; }
.grid-item:hover .grid-thumb { transform: scale(1.06); box-shadow: 0 10px 30px rgba(0,200,255,0.14); }
.grid-title { font-weight:700; font-size:14px; margin-top:8px; color:#eafcff; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.grid-meta { color:#98e9ff88; font-size:12px; margin-top:6px; }
.chk-row { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:8px; }

/* responsive */
@media (max-width: 950px) { .grid-item { width:100%; } }

/* Hide Streamlit header, footer & hamburger menu */
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden !important;}
[data-testid="stHeader"] {display: none;}
#MainMenu {visibility: hidden;}

/* hide default footer */
footer { display:none !important; }
</style>
""",
    unsafe_allow_html=True,
)

# --------- Sidebar buttons that auto-close ----------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "INSTAGRAM_COOKIE" not in st.session_state:
    st.session_state.INSTAGRAM_COOKIE = ""
if "preview_cache" not in st.session_state:
    st.session_state.preview_cache = {}
if "download_thread" not in st.session_state:
    st.session_state.download_thread = None

def set_page_and_close(page_name: str):
    st.session_state.page = page_name
    js = """
    <script>
    (function(){
      const sbToggle = window.parent.document.querySelector('button[aria-label="Toggle sidebar"]');
      if (sbToggle) { sbToggle.click(); }
    })();
    </script>
    """
    components.html(js, height=0)

with st.sidebar:
    st.markdown(f"## 🎬 {APP_TITLE}")
    st.markdown("---")
    if st.button("🏠 Home", on_click=set_page_and_close, args=("Home",)): pass
    if st.button("🔎 Any Video (MP4)", on_click=set_page_and_close, args=("AnyVideo",)): pass
    if st.button("🎧 Audio (MP3)", on_click=set_page_and_close, args=("Audio",)): pass
    if st.button("🎬 TikTok Account", on_click=set_page_and_close, args=("TikTok",)): pass
    if st.button("📸 Instagram Account", on_click=set_page_and_close, args=("Instagram",)): pass
    if st.button("⚙️ Set Instagram Cookie", on_click=set_page_and_close, args=("Cookie",)): pass
    if st.button("💡 About", on_click=set_page_and_close, args=("About",)): pass

# floating open menu button if user collapsed sidebar
open_menu_html = """
<button id="openMenuBtn" style="position:fixed;left:12px;top:12px;padding:8px 12px;border-radius:8px;border:none;background:linear-gradient(90deg,#00c2ff,#0069ff);color:#001;font-weight:700;z-index:9999;display:none;"
 onclick="
  try{
    const sbToggle = window.parent.document.querySelector('button[aria-label=\"Toggle sidebar\"]');
    if (sbToggle) sbToggle.click();
    this.style.display='none';
  }catch(e){console.log(e)}
">☰ Menu</button>
<script>
(function(){
  setTimeout(function(){
    const sb = window.parent.document.querySelector('[data-testid=\"stSidebar\"]');
    const openBtn = document.getElementById('openMenuBtn');
    if (sb && openBtn){
      const style = window.getComputedStyle(sb);
      if (style && style.display === 'none'){ openBtn.style.display='block'; }
    }
  }, 700);
})();
</script>
"""
components.html(open_menu_html, height=0)

# --------- Utility functions ----------
def human_duration(seconds: Optional[int]) -> str:
    try:
        s = int(seconds or 0)
        m = s // 60
        sec = s % 60
        return f"{m}:{sec:02d}"
    except Exception:
        return str(seconds or "")

def fetch_metadata(url: str, cookie: Optional[str] = None, limit_preview: int = 24):
    cache_key = f"{url}::cookie={bool(cookie)}::limit={limit_preview}"
    if cache_key in st.session_state.preview_cache:
        return st.session_state.preview_cache[cache_key]
    opts = {"quiet": True, "no_warnings": True}
    if cookie:
        tmp = OUT_DIR / "preview_cookie.txt"
        tmp.write_text(cookie)
        opts["cookiefile"] = str(tmp)
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if isinstance(info, dict) and "entries" in info:
                entries = [e for e in info["entries"] if isinstance(e, dict)]
                info_preview = dict(info)
                info_preview["entries"] = entries[:limit_preview]
                st.session_state.preview_cache[cache_key] = info_preview
                return info_preview
            st.session_state.preview_cache[cache_key] = info
            return info
    except Exception as e:
        st.error(f"Preview failed: {e}")
        return None

def _yt_download_worker(ydl_opts, urls: List[str], result_paths: List[str], audio=False, cookie=None, playlist_end=None):
    try:
        with YoutubeDL(ydl_opts) as ydl:
            if len(urls) == 1 and (urls[0].startswith("https://www.tiktok.com/") or urls[0].startswith("https://www.instagram.com/")):
                if playlist_end and isinstance(playlist_end, int) and playlist_end > 0:
                    ydl.params["playlistend"] = playlist_end
                res = ydl.extract_info(urls[0], download=True)
            else:
                for u in urls:
                    ydl.extract_info(u, download=True)
        now = time.time()
        for p in OUT_DIR.iterdir():
            try:
                if p.is_file() and (now - p.stat().st_mtime) < 900:
                    result_paths.append(str(p))
            except Exception:
                continue
    except Exception as e:
        result_paths.append(f"__ERROR__:{e}")

def download_with_animation(urls: List[str], audio: bool = False, cookie: Optional[str] = None, playlist_end: Optional[int] = None) -> List[str]:
    outtmpl = str(OUT_DIR / "%(title).100s.%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }
    if audio:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
        })
    else:
        ydl_opts.update({"format": "best", "merge_output_format": "mp4"})

    if cookie:
        cf = OUT_DIR / "dl_cookie.txt"
        cf.write_text(cookie)

    result_paths: List[str] = []
    worker = threading.Thread(target=_yt_download_worker, args=(ydl_opts, urls, result_paths, audio, cookie, playlist_end))
    worker.start()
    st.session_state.download_thread = worker

    progress = st.progress(0)
    status = st.empty()
    t = 0
    while worker.is_alive():
        t = (t + 7) % 100
        progress.progress(t)
        status.info("Downloading... (this is an animated progress bar)")
        time.sleep(0.18)
    progress.progress(100)
    status.success("Download finished — finalizing files...")
    time.sleep(0.6)

    downloaded = [p for p in result_paths if not p.startswith("__ERROR__")]
    errors = [p for p in result_paths if p.startswith("__ERROR__")]
    if errors:
        status.error("Some downloads failed. See logs.")
        for e in errors:
            st.text(e)
    return downloaded

# --------- UI pages ----------
st.markdown("<div class='card'>", unsafe_allow_html=True)
page = st.session_state.page

# HOME page
if page == "Home":
    st.markdown(f"<h1>🎬 {APP_TITLE}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4>{APP_TAGLINE}</h4>", unsafe_allow_html=True)
    st.markdown("---")
    if Path(HOME_HTML).exists():
        try:
            html_content = Path(HOME_HTML).read_text(encoding="utf-8")
            wrapped = f"<div style='padding:8px;background:transparent;border-radius:8px'>{html_content}</div>"
            st.components.v1.html(wrapped, height=560, scrolling=True)
        except Exception as e:
            st.error("Failed to load home.html")
            st.text(str(e))
    else:
        st.info(f"Place a '{HOME_HTML}' file in the app folder to show your landing page here.")
