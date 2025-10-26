import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import shutil
import time
import traceback
import streamlit.components.v1 as components
from typing import List, Optional
import os

# ---------------- Config ----------------
APP_TITLE = "All Video Downloader"
APP_TAGLINE = "Enjoy your downloads"
HOME_HTML = "home.html"

st.set_page_config(page_title=f"{APP_TITLE} — {APP_TAGLINE}", page_icon="🎬", layout="wide")

OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ---------------- CSS ----------------
st.markdown("""
<style>
body, .stApp {
  background: linear-gradient(180deg,#030407,#07101a);
  color: #eafcff;
  font-family: Inter, sans-serif;
}
h1,h2,h3 { text-align:center; color:#8ef0ff; }
.card { background: linear-gradient(180deg,#07121a,#08121a);
  border-radius:14px; padding:14px; margin:10px;
  box-shadow: 0 14px 46px rgba(0,0,0,0.7);
  border:1px solid rgba(0,140,255,0.06);
}
.stButton>button {
  background: linear-gradient(90deg,#00c2ff,#0069ff);
  color:white; font-weight:700; border-radius:10px;
  padding:10px 18px; width:100%;
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
.grid { display:flex; flex-wrap:wrap; gap:14px; justify-content:center; }
.grid-item { width:300px; background:linear-gradient(180deg,#08121a,#0b1720);
  border-radius:12px; padding:8px; box-shadow:0 10px 30px rgba(0,0,0,0.6);
  border:1px solid rgba(0,120,255,0.04); transition:0.2s;
}
.grid-item:hover { transform:translateY(-6px); }
footer {display:none !important;}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "INSTAGRAM_COOKIE" not in st.session_state:
    st.session_state.INSTAGRAM_COOKIE = ""

def set_page(page): st.session_state.page = page

with st.sidebar:
    st.markdown(f"## 🎬 {APP_TITLE}")
    st.divider()
    if st.button("🏠 Home"): set_page("Home")
    if st.button("🔎 Any Video (MP4)"): set_page("AnyVideo")
    if st.button("🎧 Audio (MP3)"): set_page("Audio")
    if st.button("🎬 TikTok Account"): set_page("TikTok")
    if st.button("📸 Instagram Account"): set_page("Instagram")
    if st.button("⚙️ Set Instagram Cookie"): set_page("Cookie")
    if st.button("💡 About"): set_page("About")

# ---------------- Utilities ----------------
def human_duration(seconds: Optional[int]) -> str:
    try:
        s = int(seconds or 0)
        m = s // 60
        sec = s % 60
        return f"{m}:{sec:02d}"
    except Exception:
        return str(seconds or "")

def fetch_metadata(url: str, cookie: Optional[str] = None):
    opts = {"quiet": True, "no_warnings": True}
    if cookie:
        tmp = OUT_DIR / "cookie.txt"
        tmp.write_text(cookie)
        opts["cookiefile"] = str(tmp)
    with YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

def download_with_progress(urls: List[str], audio=False, cookie=None):
    outtmpl = str(OUT_DIR / "%(title).100s.%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "progress_hooks": [],
    }
    if audio:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
        })
    else:
        ydl_opts.update({"format": "best", "merge_output_format": "mp4"})
    if cookie:
        cf = OUT_DIR / "dl_cookie.txt"
        cf.write_text(cookie)
        ydl_opts["cookiefile"] = str(cf)

    prog = st.progress(0)
    status = st.empty()

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            dl = d.get("downloaded_bytes", 0)
            if total:
                pct = int(dl * 100 / total)
                prog.progress(min(pct, 100))
                status.info(f"Downloading {pct}%")
        elif d["status"] == "finished":
            prog.progress(100)
            status.success("Finalizing...")

    ydl_opts["progress_hooks"].append(hook)

    with YoutubeDL(ydl_opts) as ydl:
        for u in urls:
            ydl.download([u])

    prog.empty()
    status.success("✅ Done!")
    files = sorted(OUT_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in files[:len(urls)]]

# ---------------- Pages ----------------
page = st.session_state.page
st.markdown("<div class='card'>", unsafe_allow_html=True)

# HOME
if page == "Home":
    st.title(APP_TITLE)
    st.write(APP_TAGLINE)
    if Path(HOME_HTML).exists():
        st.components.v1.html(Path(HOME_HTML).read_text(), height=500)

# ANY VIDEO
elif page == "AnyVideo":
    st.subheader("🎞️ Download Any Video (MP4)")
    url = st.text_input("Paste video URL", key="vid_url")
    if st.button("Submit (MP4)"):
        if url:
            with st.spinner("Fetching video info..."):
                info = fetch_metadata(url)
                title = info.get("title")
                st.write(f"**Title:** {title}")
                if st.button("⬇️ Download Video"):
                    files = download_with_progress([url])
                    for f in files:
                        with open(f, "rb") as fh:
                            st.download_button("⬇️ Save File", fh, file_name=Path(f).name)

# AUDIO
elif page == "Audio":
    st.subheader("🎧 Extract Audio (MP3)")
    url = st.text_input("Paste video URL", key="aud_url")
    if st.button("Submit (MP3)"):
        if url:
            info = fetch_metadata(url)
            st.write(f"**Title:** {info.get('title','No title')}")
            if st.button("⬇️ Download Audio"):
                files = download_with_progress([url], audio=True)
                for f in files:
                    with open(f, "rb") as fh:
                        st.download_button("⬇️ Save MP3", fh, file_name=Path(f).name)

# TIKTOK
elif page == "TikTok":
    st.subheader("🎬 TikTok Account")
    user = st.text_input("Enter TikTok username (without @)")
    if st.button("Submit TikTok"):
        if user:
            profile_url = f"https://www.tiktok.com/@{user}"
            info = fetch_metadata(profile_url)
            entries = info.get("entries", [])
            total = len(entries)
            st.info(f"Found {total} videos.")
            limit = st.number_input("How many videos to download?", 1, min(2, total), 1)
            if st.button("⬇️ Download Selected TikToks"):
                urls = [e["webpage_url"] for e in entries[:int(limit)]]
                files = download_with_progress(urls)
                zip_name = OUT_DIR / f"{user}_videos.zip"
                shutil.make_archive(str(zip_name.with_suffix('')), 'zip', root_dir=OUT_DIR)
                with open(f"{zip_name}", "rb") as zf:
                    st.download_button("📦 Download ZIP", zf, file_name=zip_name.name)

# INSTAGRAM
elif page == "Instagram":
    st.subheader("📸 Instagram Account")
    user = st.text_input("Enter Instagram username (without @)")
    cookie = st.session_state.INSTAGRAM_COOKIE
    if st.button("Submit Instagram"):
        if user:
            profile_url = f"https://www.instagram.com/{user}/"
            info = fetch_metadata(profile_url, cookie)
            entries = info.get("entries", [])
            total = len(entries)
            st.info(f"Found {total} posts.")
            limit = st.number_input("How many posts to download?", 1, min(2, total), 1)
            if st.button("⬇️ Download Selected Posts"):
                urls = [e["webpage_url"] for e in entries[:int(limit)]]
                files = download_with_progress(urls, cookie=cookie)
                zip_name = OUT_DIR / f"{user}_posts.zip"
                shutil.make_archive(str(zip_name.with_suffix('')), 'zip', root_dir=OUT_DIR)
                with open(f"{zip_name}", "rb") as zf:
                    st.download_button("📦 Download ZIP", zf, file_name=zip_name.name)

# COOKIE
elif page == "Cookie":
    st.subheader("⚙️ Instagram Cookie")
    cookie_val = st.text_area("Paste cookie string", value=st.session_state.INSTAGRAM_COOKIE)
    if st.button("Save Cookie"):
        st.session_state.INSTAGRAM_COOKIE = cookie_val
        st.success("Cookie saved for this session.")

# ABOUT
elif page == "About":
    st.subheader("💡 About")
    st.markdown("""
    - Auto preview thumbnails and metadata for any URL  
    - Grid preview & ZIP download for TikTok and Instagram  
    - Direct Chrome download buttons  
    - Built with **Streamlit + yt-dlp**  
    - Developer: **Tanzeel ur Rehman**
    """)

st.markdown("</div>", unsafe_allow_html=True)
