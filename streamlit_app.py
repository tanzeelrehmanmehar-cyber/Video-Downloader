# app.py
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import shutil
import time
import traceback
import streamlit.components.v1 as components
from typing import List, Optional
import tempfile
import os

# ---------------- Config ----------------
APP_TITLE = "All Video Downloader"
APP_TAGLINE = "Enjoy"
HOME_HTML = "home.html"  # path to your home.html (same folder)

st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_TAGLINE}",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ---------------- CSS (dark neon + hover + layout) ----------------
st.markdown(
    f"""
<style>
/* base */
body, .stApp {{ background: linear-gradient(180deg,#030407,#07101a); color: #eafcff; font-family: Inter, sans-serif; }}
h1,h2,h3 {{ text-align:center; color:#8ef0ff; }}
.card {{ background: linear-gradient(180deg,#07121a,#08121a); border-radius:14px; padding:14px; margin:10px; box-shadow: 0 14px 46px rgba(0,0,0,0.7); border:1px solid rgba(0,140,255,0.06); }}
.stButton>button {{ background: linear-gradient(90deg,#00c2ff,#0069ff); color: white; font-weight:700; border-radius:10px; padding:10px 18px; width:100%; box-shadow:0 8px 20px rgba(0,100,255,0.18); }}
.stButton>button:hover {{ transform: translateY(-3px); }}
input[type=text], textarea {{ background:#07111a !important; color:#eafcff !important; border-radius:8px !important; padding:10px !important; border:1px solid #183045 !important; }}
/* grid */
.grid {{ display:flex; flex-wrap:wrap; gap:14px; justify-content:center; margin-top:12px; }}
.grid-item {{ width: 300px; background: linear-gradient(180deg,#08121a,#0b1720); border-radius:12px; padding:8px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); transition: transform .18s ease, box-shadow .18s ease; border:1px solid rgba(0,120,255,0.04); }}
.grid-item:hover {{ transform: translateY(-6px); box-shadow: 0 18px 40px rgba(0,140,255,0.12); }}
.grid-thumb {{ width:100%; height:170px; object-fit:cover; border-radius:8px; transition: transform .22s ease, box-shadow .22s ease; }}
.grid-item:hover .grid-thumb {{ transform: scale(1.06); box-shadow: 0 10px 30px rgba(0,200,255,0.14); }}
.grid-title {{ font-weight:700; font-size:14px; margin-top:8px; color:#eafcff; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.grid-meta {{ color:#98e9ff88; font-size:12px; margin-top:6px; }}
.chk-row {{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:8px; }}
@media (max-width: 950px) {{ .grid-item {{ width:100%; }} }}
/* thumbnail hover larger preview: we use a simple shadow/scale - Streamlit doesn't support complex :hover popups reliably */
footer {{ display:none !important; }}
/* sidebar button look is handled by using st.button in sidebar */
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Sidebar menu (buttons that auto-close) ----------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "INSTAGRAM_COOKIE" not in st.session_state:
    st.session_state.INSTAGRAM_COOKIE = ""
if "preview_cache" not in st.session_state:
    st.session_state.preview_cache = {}  # simple cache for metadata
if "last_downloaded" not in st.session_state:
    st.session_state.last_downloaded = []

# helper to set page and auto-close sidebar
def set_page_and_close(page_name: str):
    st.session_state.page = page_name
    # JS: click the sidebar toggle button to collapse it
    js = """
    <script>
    (function(){
      const sbToggle = window.parent.document.querySelector('button[aria-label="Toggle sidebar"]');
      if (sbToggle){ sbToggle.click(); }
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

# floating "open menu" button (appears when sidebar is closed)
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

# ---------------- Utilities ----------------
def human_duration(seconds: Optional[int]) -> str:
    try:
        s = int(seconds or 0)
        m = s // 60
        sec = s % 60
        return f"{m}:{sec:02d}"
    except Exception:
        return str(seconds or "")

def fetch_metadata(url: str, cookie: Optional[str] = None, limit_preview: int = 24):
    """
    Use yt-dlp to extract metadata (no download).
    Caches results in session_state.preview_cache to avoid repeated requests.
    """
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
            # crop entries if profile/playlist
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

def download_with_progress(urls: List[str], audio: bool = False, cookie: Optional[str] = None, playlist_end: Optional[int] = None):
    """
    Download a list of URLs or a single profile/playlist URL with yt-dlp.
    Returns list of saved file paths.
    """
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
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
        })
    else:
        ydl_opts.update({"format": "best", "merge_output_format": "mp4"})

    if cookie:
        cf = OUT_DIR / "dl_cookie.txt"
        cf.write_text(cookie)
        ydl_opts["cookiefile"] = str(cf)

    prog = st.progress(0)
    status = st.empty()
    downloaded = []

    def hook(d):
        s = d.get("status")
        if s == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            dl = d.get("downloaded_bytes", 0)
            if total:
                pct = int(dl * 100 / total)
                prog.progress(min(pct, 100))
                status.info(f"Downloading — {pct}%")
            else:
                prog.progress(5)
                status.info(f"Downloading — {dl} bytes")
        elif s == "finished":
            prog.progress(100)
            status.success("Finalizing...")
        elif s == "error":
            status.error("Error during download")

    ydl_opts["progress_hooks"].append(hook)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # If it's a single profile URL (TikTok/Instagram) pass it directly
            if len(urls) == 1 and (urls[0].startswith("https://www.tiktok.com/") or urls[0].startswith("https://www.instagram.com/")):
                if playlist_end and isinstance(playlist_end, int) and playlist_end > 0:
                    ydl_opts["playlistend"] = playlist_end
                res = ydl.extract_info(urls[0], download=True)
            else:
                for u in urls:
                    ydl.extract_info(u, download=True)
            # find recent files (within last 15 minutes)
            now = time.time()
            candidates = []
            for p in OUT_DIR.iterdir():
                try:
                    if p.is_file() and (now - p.stat().st_mtime) < 900:
                        candidates.append(p)
                except Exception:
                    continue
            downloaded = sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True)
            prog.empty()
            if downloaded:
                status.success("✅ Downloads finished")
            else:
                status.warning("No files detected after download")
            return [str(p) for p in downloaded]
    except Exception as e:
        prog.empty()
        st.error(f"Download failed: {e}")
        st.error(traceback.format_exc())
        return []

# ---------------- UI Pages ----------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
page = st.session_state.page

# HOME: embed home.html, but apply the theme wrapper
if page == "Home":
    st.markdown(f"<h1>🎬 {APP_TITLE}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4>{APP_TAGLINE}</h4>", unsafe_allow_html=True)
    st.markdown("---")
    if Path(HOME_HTML).exists():
        try:
            html_content = Path(HOME_HTML).read_text(encoding="utf-8")
            # wrap home.html content into a themed container with small padding
            wrapped = f"<div style='padding:8px;background:transparent;border-radius:8px'>{html_content}</div>"
            st.components.v1.html(wrapped, height=600, scrolling=True)
        except Exception as e:
            st.error("Failed to load home.html")
            st.text(str(e))
    else:
        st.info(f"Place your custom '{HOME_HTML}' file in the app folder to show a landing page here.")
    st.markdown("---")
    recent = sorted(list(OUT_DIR.glob("*")), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
    if recent:
        st.write("Recent downloads (click to save):")
        cols = st.columns(min(3, len(recent)))
        for i, f in enumerate(recent):
            with cols[i % len(cols)]:
                st.write(f.name)
                with open(f, "rb") as fh:
                    st.download_button("⬇️ Save", data=fh, file_name=f.name)

# ANY VIDEO (MP4): auto-preview + download + thumbnail + progress
elif page == "AnyVideo":
    st.markdown("<h2>🎞️ Download Any Video (MP4)</h2>", unsafe_allow_html=True)
    url = st.text_input("Paste video / reel URL (YouTube, TikTok, Instagram, etc.)", key="any_video_url")
    if url and url.strip():
        with st.spinner("Fetching preview..."):
            info = fetch_metadata(url.strip(), limit_preview=1)
        if info:
            entry = info["entries"][0] if isinstance(info, dict) and "entries" in info else info
            title = entry.get("title", "No title")
            thumb = entry.get("thumbnail")
            uploader = entry.get("uploader") or entry.get("uploader_id", "")
            duration = human_duration(entry.get("duration"))
            c1, c2 = st.columns([1, 2])
            with c1:
                if thumb:
                    st.image(thumb, use_column_width=True)
            with c2:
                st.markdown(f"**{title}**")
                st.write(f"Uploader: {uploader}")
                st.write(f"Duration: {duration}")
            st.markdown("---")
            if st.button("⬇️ Download MP4"):
                files = download_with_progress([url.strip()], audio=False)
                if files:
                    st.success(f"Downloaded {len(files)} file(s).")
                    for f in files:
                        with open(f, "rb") as fh:
                            st.download_button("⬇️ Save file", data=fh, file_name=Path(f).name)

# AUDIO (MP3)
elif page == "Audio":
    st.markdown("<h2>🎧 Extract Audio (MP3)</h2>", unsafe_allow_html=True)
    url = st.text_input("Paste video URL to extract audio", key="audio_url")
    if url and url.strip():
        with st.spinner("Fetching preview..."):
            info = fetch_metadata(url.strip(), limit_preview=1)
        if info:
            entry = info["entries"][0] if isinstance(info, dict) and "entries" in info else info
            st.markdown(f"**{entry.get('title','No title')}**")
            if entry.get("thumbnail"):
                st.image(entry.get("thumbnail"), width=360)
            st.write(f"Uploader: {entry.get('uploader') or ''}")
        if st.button("⬇️ Download MP3"):
            files = download_with_progress([url.strip()], audio=True)
            if files:
                st.success("Audio downloaded.")
                for f in files:
                    with open(f, "rb") as fh:
                        st.download_button("⬇️ Save audio", data=fh, file_name=Path(f).name)

# TIKTOK Account: grid preview, select/deselect all visible, quick select N, ZIP download
elif page == "TikTok":
    st.markdown("<h2>🎬 TikTok Account — Grid Preview</h2>", unsafe_allow_html=True)
    username = st.text_input("Enter TikTok username (without @)", key="tt_user")
    if username and username.strip():
        account_url = f"https://www.tiktok.com/@{username.strip()}"
        preview_limit = st.slider("Preview first N videos", 3, 36, 12, 3, key="tt_preview")
        with st.spinner("Fetching preview..."):
            info = fetch_metadata(account_url, limit_preview=preview_limit)
        entries = info.get("entries") if info and isinstance(info, dict) else None
        if not entries:
            st.info("No preview available — the account may be private or blocked. Try setting cookie under 'Set Instagram Cookie'.")
        else:
            st.write(f"Showing {len(entries)} items from @{username.strip()}")
            # selection controls
            c_a, c_b, c_c = st.columns([1, 1, 2])
            with c_a:
                if st.button("Select All Visible (TikTok)"):
                    for idx in range(len(entries)):
                        st.session_state[f"tt_chk_{idx}"] = True
                    st.experimental_rerun()
            with c_b:
                if st.button("Deselect All Visible (TikTok)"):
                    for idx in range(len(entries)):
                        st.session_state[f"tt_chk_{idx}"] = False
                    st.experimental_rerun()
            with c_c:
                select_first = st.number_input("Quick select first N", min_value=0, max_value=len(entries), value=0, step=1, key="tt_quick")
                if st.button("Apply Quick Select (TikTok)"):
                    for idx in range(len(entries)):
                        st.session_state[f"tt_chk_{idx}"] = True if idx < select_first else False
                    st.experimental_rerun()

            # grid
            st.markdown("<div class='grid'>", unsafe_allow_html=True)
            selected_urls = []
            for idx, e in enumerate(entries):
                url_item = e.get("webpage_url") or e.get("url") or e.get("id")
                key = f"tt_chk_{idx}"
                default = st.session_state.get(key, False)
                # item card
                st.markdown("<div class='grid-item'>", unsafe_allow_html=True)
                if e.get("thumbnail"):
                    st.image(e.get("thumbnail"), use_column_width=True)
                st.markdown(f"<div class='grid-title'>{(e.get('title') or '')[:80]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='grid-meta'>{human_duration(e.get('duration'))} • {e.get('uploader') or ''}</div>", unsafe_allow_html=True)
                chk = st.checkbox("Select", value=default, key=key)
                if chk:
                    selected_urls.append(url_item)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("⬇️ Download Selected & Create ZIP (TikTok)"):
                if not selected_urls:
                    st.warning("No items selected.")
                else:
                    st.info(f"Downloading {len(selected_urls)} selected items...")
                    files = download_with_progress(selected_urls, audio=False)
                    if files:
                        # create zip of selected files only
                        tmp_dir = OUT_DIR / f"tmp_zip_{int(time.time())}"
                        tmp_dir.mkdir(exist_ok=True)
                        for f in files:
                            src = Path(f)
                            if src.exists():
                                shutil.copy(src, tmp_dir / src.name)
                        zip_name = OUT_DIR / f"{username.strip()}_selected_{int(time.time())}.zip"
                        shutil.make_archive(str(zip_name.with_suffix('')), 'zip', root_dir=tmp_dir)
                        # cleanup tmp
                        shutil.rmtree(tmp_dir)
                        st.success(f"ZIP created: {zip_name.name}")
                        with open(zip_name, "rb") as zf:
                            st.download_button("⬇️ Download ZIP", data=zf, file_name=zip_name.name)
‎elif page == "Instagram":
‎    st.markdown("<h2>📸 Instagram Account — Grid Preview</h2>", unsafe_allow_html=True)
‎    ig_user = st.text_input("Enter Instagram username (without @)", key="ig_user")
‎    if ig_user and ig_user.strip():
‎        profile_url = f"https://www.instagram.com/{ig_user.strip()}/"
‎        preview_limit = st.slider("Preview first N posts", 3, 36, 12, 3, key="ig_preview")
‎        cookie = st.session_state.INSTAGRAM_COOKIE or None
‎        with st.spinner("Fetching profile preview (may require cookie for private accounts)..."):
‎            info = fetch_metadata(profile_url, cookie=cookie, limit_preview=preview_limit)
‎        entries = info.get("entries") if info and isinstance(info, dict) else None
‎        if not entries:
‎            st.info("No preview entries. Profile may be private or blocked. Try setting cookie under 'Set Instagram Cookie'.")
‎        else:
‎            st.write(f"Showing {len(entries)} items from @{ig_user.strip()}")
‎            c_a, c_b, c_c = st.columns([1, 1, 2])
‎            with c_a:
‎                if st.button("Select All Visible (IG)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"ig_chk_{idx}"] = True
‎                    st.experimental_rerun()
‎            with c_b:
‎                if st.button("Deselect All Visible (IG)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"ig_chk_{idx}"] = False
‎                    st.experimental_rerun()
‎            with c_c:
‎                select_first = st.number_input("Quick select first N", min_value=0, max_value=len(entries), value=0, step=1, key="ig_quick")
‎                if st.button("Apply Quick Select (IG)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"ig_chk_{idx}"] = True if idx < select_first else False
‎                    st.experimental_rerun()
‎
‎            # grid
‎            st.markdown("<div class='grid'>", unsafe_allow_html=True)
‎            selected_urls = []
‎            for idx, e in enumerate(entries):
‎                url_item = e.get("webpage_url") or e.get("url") or e.get("id")
‎                key = f"ig_chk_{idx}"
‎                default = st.session_state.get(key, False)
‎                st.markdown("<div class='grid-item'>", unsafe_allow_html=True)
‎                if e.get("thumbnail"):
‎                    st.image(e.get("thumbnail"), use_column_width=True)
‎                st.markdown(f"<div class='grid-title'>{(e.get('title') or '')[:80]}</div>", unsafe_allow_html=True)
‎                st.markdown(f"<div class='grid-meta'>{human_duration(e.get('duration'))} • {e.get('uploader') or ''}</div>", unsafe_allow_html=True)
‎                chk = st.checkbox("Select", value=default, key=key)
‎                if chk:
‎                    selected_urls.append(url_item)
‎                st.markdown("</div>", unsafe_allow_html=True)
‎            st.markdown("</div>", unsafe_allow_html=True)
‎
‎            if st.button("⬇️ Download Selected & Create ZIP (IG)"):
‎                if not selected_urls:
‎                    st.warning("No posts selected.")
‎                else:
‎                    st.info(f"Downloading {len(selected_urls)} selected posts...")
‎                    files = download_with_progress(selected_urls, audio=False, cookie=cookie)
‎                    if files:
‎                        tmp_dir = OUT_DIR / f"tmp_zip_ig_{int(time.time())}"
‎                        tmp_dir.mkdir(exist_ok=True)
‎                        for f in files:
‎                            src = Path(f)
‎                            if src.exists():
‎                                shutil.copy(src, tmp_dir / src.name)
‎                        zip_name = OUT_DIR / f"{ig_user.strip()}_selected_{int(time.time())}.zip"
‎                        shutil.make_archive(str(zip_name.with_suffix('')), 'zip', root_dir=tmp_dir)
‎                        shutil.rmtree(tmp_dir)
‎                        st.success(f"ZIP created: {zip_name.name}")
‎                        with open(zip_name, "rb") as zf:
‎                            st.download_button("⬇️ Download ZIP", data=zf, file_name=zip_name.name)
‎
‎# COOKIE
‎elif page == "Cookie":
‎    st.markdown("<h2>⚙️ Instagram Cookie (optional)</h2>", unsafe_allow_html=True)
‎    st.markdown("If profiles are private or preview fails, paste a full cookie string here (sessionid=...; csrftoken=...; ...). Keep this private.")
‎    cookie_val = st.text_area("Paste cookie string", value=st.session_state.INSTAGRAM_COOKIE, height=140)
‎    if st.button("Save Cookie"):
‎        if cookie_val and cookie_val.strip():
‎            st.session_state.INSTAGRAM_COOKIE = cookie_val.strip()
‎            st.success("Cookie saved for this session.")
‎        else:
‎            st.warning("Paste a non-empty cookie string.")
‎
‎# ABOUT
‎elif page == "About":
‎    st.markdown("<h2>💡 About</h2>", unsafe_allow_html=True)
‎    st.write("""
‎- **Auto-preview** thumbnails & metadata for any URL.  
‎- **Grid preview** for TikTok & Instagram accounts (thumbnail hover, select/deselect all).  
‎- **Download selected items** and receive a single **ZIP** containing chosen videos.  
‎- Built with **Streamlit + yt-dlp**.  
‎- Developer: **Tanzeel ur Rehman**
‎""")
‎    st.markdown("---")
‎    recent = sorted(list(OUT_DIR.glob("*")), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
‎    if recent:
‎        st.write("Recent downloads:")
‎        cols = st.columns(min(3, len(recent)))
‎        for i, f in enumerate(recent):
‎            with cols[i % len(cols)]:
‎                st.write(f.name)
‎                with open(f, "rb") as fh:
‎                    st.download_button("⬇️ Save", data=fh, file_name=f.name)
‎
‎st.markdown("</div>", unsafe_allow_html=True)
