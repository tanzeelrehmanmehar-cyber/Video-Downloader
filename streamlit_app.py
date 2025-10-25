# app.py
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import time
import traceback
import math
import streamlit.components.v1 as components

# ----------------- Config -----------------
st.set_page_config(page_title="Universal Downloader (Pro Grid)",
                   page_icon="🎥",
                   layout="wide",
                   initial_sidebar_state="expanded")

OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ----------------- CSS -----------------
st.markdown(
    """
<style>
/* Page background and fonts */
body, .stApp { background: linear-gradient(180deg,#060607,#07101a); color: #e9fbff; font-family: Inter, sans-serif; }

/* Card / panel */
.card {
  background: linear-gradient(180deg,#0b1220,#08101a);
  border-radius:14px; padding:14px; margin:10px; box-shadow: 0 12px 36px rgba(0,0,0,0.6);
  border: 1px solid rgba(0,124,255,0.06);
}

/* Title center */
h1, h2 { text-align:center; color:#8ef0ff; }

/* Buttons */
.stButton>button {
  background: linear-gradient(90deg,#00c2ff,#0069ff);
  color: white; font-weight:700; border-radius:10px; padding:10px 18px;
  box-shadow: 0 8px 20px rgba(0,100,255,0.18);
}

/* Sidebar buttons look */
.sidebar-btn {
  display:block; width:100%; padding:10px; margin:6px 0; text-align:center;
  border-radius:8px; font-weight:700; color:#e8faff; background:#071528; border:1px solid #0f3a5a;
}
.sidebar-btn:hover { background:#0b466f; cursor:pointer; }

/* Grid preview */
.grid { display:flex; flex-wrap:wrap; margin-top:12px; gap:12px; justify-content:center; }
.grid-item { width: 300px; background: linear-gradient(180deg,#08121a,#0b1922); border-radius:12px; padding:8px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
.grid-thumb { width:100%; border-radius:8px; box-shadow: 0 6px 18px rgba(0,120,255,0.12); }
.grid-title { font-weight:700; font-size:14px; margin-top:8px; color:#dff9ff; }
.grid-meta { color:#98e9ff88; font-size:12px; margin-top:6px; }

/* Responsive (small screens) */
@media (max-width: 900px) {
  .grid-item { width: 100%; }
}

/* hide footer */
footer { display:none !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------- Sidebar (styled as buttons) -----------------
if "menu_prev" not in st.session_state:
    st.session_state.menu_prev = None

if "page" not in st.session_state:
    st.session_state.page = "Home"

def set_page_and_close(page_name):
    st.session_state.page = page_name
    # close sidebar by toggling Streamlit's hide button via JS
    js = """
    <script>
    (function(){
      const sbToggle = window.parent.document.querySelector('button[aria-label="Toggle sidebar"]');
      if (sbToggle && sbToggle.getAttribute('data-closed') !== 'true') { sbToggle.click(); }
    })();
    </script>
    """
    components.html(js, height=0)

with st.sidebar:
    st.markdown("## 🎬 Universal Downloader")
    if st.button("🏠 Home", key="s_home", help="Go to Home", on_click=set_page_and_close, args=("Home",)):
        pass
    if st.button("🎞️ Any Video (MP4)", key="s_any", on_click=set_page_and_close, args=("AnyVideo",)):
        pass
    if st.button("🎵 Audio (MP3)", key="s_audio", on_click=set_page_and_close, args=("Audio",)):
        pass
    if st.button("🎬 TikTok Account", key="s_tt", on_click=set_page_and_close, args=("TikTok",)):
        pass
    if st.button("📸 Instagram Account", key="s_ig", on_click=set_page_and_close, args=("Instagram",)):
        pass
    if st.button("⚙️ Set Instagram Cookie", key="s_cookie", on_click=set_page_and_close, args=("Cookie",)):
        pass
    if st.button("💡 About", key="s_about", on_click=set_page_and_close, args=("About",)):
        pass

# Floating re-open menu button (only visible after sidebar is closed)
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
  // show the open button if sidebar hidden
  setTimeout(function(){
    const sb = window.parent.document.querySelector('[data-testid=\"stSidebar\"]');
    const openBtn = document.getElementById('openMenuBtn');
    if (sb && openBtn) {
      const style = window.getComputedStyle(sb);
      if (style && style.display === 'none') { openBtn.style.display='block'; }
    }
  }, 600);
})();
</script>
"""
components.html(open_menu_html, height=0)

# -------------- Helper functions ---------------
def human_duration(seconds):
    try:
        s = int(seconds)
        m = s // 60
        sec = s % 60
        return f"{m}:{sec:02d}"
    except Exception:
        return str(seconds)

def fetch_info(url, cookie: str|None=None, limit_preview:int|None=12):
    """Extract metadata (no download). Returns dict or None."""
    opts = {"quiet": True, "no_warnings": True}
    if cookie:
        tmp = OUT_DIR / "preview_cookie.txt"
        tmp.write_text(cookie)
        opts["cookiefile"] = str(tmp)
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # if playlist/profile, crop entries
            if isinstance(info, dict) and "entries" in info:
                entries = [e for e in info["entries"] if isinstance(e, dict)]
                if limit_preview and len(entries) > limit_preview:
                    info_preview = dict(info)
                    info_preview["entries"] = entries[:limit_preview]
                    return info_preview
            return info
    except Exception as e:
        st.error(f"Preview failed: {e}")
        return None

def download_with_progress(urls:list, audio=False, cookie: str|None=None, playlist_end:int|None=None):
    """Download URLs or playlist/profile using yt-dlp with progress hooks.
       urls can be a list of clicked specific entries (direct video links) or a single profile URL.
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
            "format":"bestaudio/best",
            "postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
        })
    else:
        ydl_opts.update({"format":"best","merge_output_format":"mp4"})

    if cookie:
        cf = OUT_DIR / "dl_cookie.txt"
        cf.write_text(cookie)
        ydl_opts["cookiefile"] = str(cf)

    # Progress UI
    prog = st.progress(0)
    status = st.empty()
    downloaded = []

    def hook(d):
        st.write()  # tiny layout adjust
        s = d.get("status")
        if s == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes",0)
            if total:
                pct = int(done * 100 / total)
                prog.progress(min(pct,100))
                status.info(f"Downloading {pct}%")
            else:
                prog.progress(5)
                status.info(f"Downloading... {done} bytes")
        elif s == "finished":
            prog.progress(100)
            status.success("Merging/Finalizing...")
        elif s == "error":
            status.error("Error during download")

    ydl_opts["progress_hooks"].append(hook)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # if list contains a profile URL (single) we pass it directly; if contains direct video URLs we pass them all
            if len(urls) == 1 and (urls[0].startswith("https://www.tiktok.com/") or urls[0].startswith("https://www.instagram.com/") or urls[0].endswith("/")):
                # treat as profile/playlist URL — yt-dlp will download entries; support limiting with playlistend
                if playlist_end and isinstance(playlist_end,int) and playlist_end>0:
                    ydl_opts["playlistend"] = playlist_end
                res = ydl.extract_info(urls[0], download=True)
            else:
                # download each URL
                res = None
                for u in urls:
                    ydl.extract_info(u, download=True)
            # detect recent files
            now = time.time()
            paths = []
            for p in OUT_DIR.iterdir():
                try:
                    if p.is_file() and (now - p.stat().st_mtime) < 600:  # within 10 min
                        paths.append(p)
                except Exception:
                    continue
            downloaded = sorted(set(paths), key=lambda p: p.stat().st_mtime, reverse=True)
            # present results
            if downloaded:
                status.success("✅ Download(s) completed")
            else:
                status.warning("No output files found after download")
            prog.empty()
            return [str(p) for p in downloaded]
    except Exception as e:
        prog.empty()
        st.error(f"Download failed: {e}")
        st.error(traceback.format_exc())
        return []

# -------------- UI Pages --------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
page = st.session_state.page

# HOME
if page == "Home":
    st.markdown("<h1>🎬 Universal Downloader — Pro Grid</h1>", unsafe_allow_html=True)
    st.write("Paste any video URL in the specific pages. For account/profile pages (TikTok/Instagram) you'll get a grid preview of posts — pick which ones to download via checkboxes or quickly select the first N items with the slider.")
    st.write("Files are saved into the `downloads/` folder — download buttons will let you save them locally.")
    st.markdown("---")
    recent = sorted(list(OUT_DIR.glob("*")), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
    if recent:
        st.write("Recent files:")
        cols = st.columns(min(3, len(recent)))
        for i, f in enumerate(recent):
            with cols[i % len(cols)]:
                st.write(f.name)
                with open(f, "rb") as fh:
                    st.download_button("⬇️", data=fh, file_name=f.name)
    else:
        st.info("No downloads yet in this container.")

# ANY VIDEO (single)
elif page == "AnyVideo":
    st.markdown("<h2>🎞️ Download Any Video (MP4)</h2>", unsafe_allow_html=True)
    url = st.text_input("Paste video URL (YouTube / TikTok / Instagram / etc.)", key="any_video_url")
    if url and url.strip():
        with st.spinner("Fetching preview..."):
            info = fetch_info(url.strip(), limit_preview=1)
        if info:
            # single video or playlist first item
            if isinstance(info, dict) and "entries" in info and info["entries"]:
                e = info["entries"][0]
            else:
                e = info
            title = e.get("title","(no title)")
            uploader = e.get("uploader") or e.get("uploader_id","")
            duration = human_duration(e.get("duration",0))
            thumb = e.get("thumbnail")
            cols = st.columns([1,2])
            with cols[0]:
                if thumb:
                    st.image(thumb, use_column_width=True)
            with cols[1]:
                st.markdown(f"**{title}**")
                st.write(f"Uploader: {uploader}")
                st.write(f"Duration: {duration}")
            st.markdown("---")
            if st.button("Download MP4"):
                files = download_with_progress([url.strip()], audio=False)
                if files:
                    for f in files:
                        with open(f, "rb") as fh:
                            st.download_button("⬇️ Download File", data=fh, file_name=Path(f).name)
    else:
        st.info("Paste a URL to preview the video automatically.")

# AUDIO
elif page == "Audio":
    st.markdown("<h2>🎵 Extract Audio (MP3)</h2>", unsafe_allow_html=True)
    url = st.text_input("Paste video URL to extract audio", key="audio_url")
    if url and url.strip():
        with st.spinner("Fetching preview..."):
            info = fetch_info(url.strip(), limit_preview=1)
        if info:
            e = info["entries"][0] if isinstance(info, dict) and "entries" in info else info
            st.markdown(f"**{e.get('title','(no title)')}**")
            if e.get("thumbnail"):
                st.image(e.get("thumbnail"), width=360)
            st.write(f"Uploader: {e.get('uploader') or ''}")
        if st.button("Download MP3"):
            files = download_with_progress([url.strip()], audio=True)
            if files:
                for f in files:
                    with open(f, "rb") as fh:
                        st.download_button("⬇️ Download Audio", data=fh, file_name=Path(f).name)

# TIKTOK ACCOUNT (grid preview + selection)
elif page == "TikTok":
    st.markdown("<h2>🎬 TikTok Account — Grid Preview</h2>", unsafe_allow_html=True)
    username = st.text_input("Enter TikTok username (without @)", key="tt_user")
    if username and username.strip():
        account_url = f"https://www.tiktok.com/@{username.strip()}"
        preview_limit = st.slider("Preview first N videos", min_value=3, max_value=36, value=12, step=3)
        with st.spinner("Fetching account preview..."):
            info = fetch_info(account_url, limit_preview=preview_limit)
        entries = info.get("entries") if info and isinstance(info, dict) else None
        if not entries:
            st.info("No preview available — account may be private or blocked. Try setting cookie or check username.")
        else:
            st.write(f"Showing {len(entries)} preview items from @{username.strip()}")
            # selection controls
            select_first_n = st.number_input("Quick select: Download first N items", min_value=0, max_value=len(entries), value=0, step=1)
            manual_select = []
            cols = st.columns(3)
            check_states = {}
            # render grid
            for idx, e in enumerate(entries):
                col = cols[idx % 3]
                with col:
                    thumb = e.get("thumbnail")
                    if thumb:
                        st.image(thumb, width=300)
                    st.markdown(f"**{e.get('title','(no title)')}**")
                    st.markdown(f"<div style='color:#9fe9ff'>{human_duration(e.get('duration',0))} • {e.get('uploader') or ''}</div>", unsafe_allow_html=True)
                    key = f"tt_chk_{idx}"
                    checked_default = True if (select_first_n and idx < select_first_n) else False
                    chk = st.checkbox("Select", value=checked_default, key=key)
                    if chk:
                        manual_select.append(e.get("webpage_url") or e.get("url") or e.get("id"))
            st.markdown("---")
            download_btn = st.button("⬇️ Download Selected TikTok Videos")
            if download_btn:
                if not manual_select:
                    st.warning("No videos selected. Use the checkboxes or 'Quick select' to pick items.")
                else:
                    st.info(f"Downloading {len(manual_select)} selected items...")
                    files = download_with_progress(manual_select, audio=False)
                    if files:
                        for f in files:
                            with open(f, "rb") as fh:
                                st.download_button("⬇️ " + Path(f).name, data=fh, file_name=Path(f).name)

# INSTAGRAM ACCOUNT (grid preview + selection)
elif page == "Instagram":
    st.markdown("<h2>📸 Instagram Account — Grid Preview</h2>", unsafe_allow_html=True)
    ig_user = st.text_input("Enter Instagram username (without @)", key="ig_user_field")
    if ig_user and ig_user.strip():
        profile_url = f"https://www.instagram.com/{ig_user.strip()}/"
        preview_limit = st.slider("Preview first N posts", min_value=3, max_value=36, value=12, step=3, key="ig_preview_slider")
        cookie = st.session_state.get("INSTAGRAM_COOKIE") or None
        with st.spinner("Fetching profile preview (may require cookie for private accounts)..."):
            info = fetch_info(profile_url, cookie=cookie, limit_preview=preview_limit)
        entries = info.get("entries") if info and isinstance(info, dict) else None
        if not entries:
            st.info("No preview entries found. The profile may be private or blocked. Try setting cookie in the 'Set Instagram Cookie' tab.")
        else:
            st.write(f"Showing {len(entries)} preview items from @{ig_user.strip()}")
            select_first_n = st.number_input("Quick select: Download first N items", min_value=0, max_value=len(entries), value=0, step=1, key="ig_quick_select")
            manual_select = []
            cols = st.columns(3)
            for idx, e in enumerate(entries):
                col = cols[idx % 3]
                with col:
                    thumb = e.get("thumbnail")
                    if thumb:
                        st.image(thumb, width=300)
                    st.markdown(f"**{e.get('title','(no title)')}**")
                    st.markdown(f"<div style='color:#9fe9ff'>{human_duration(e.get('duration',0))} • {e.get('uploader') or ''}</div>", unsafe_allow_html=True)
                    key = f"ig_chk_{idx}"
                    checked_default = True if (select_first_n and idx < select_first_n) else False
                    chk = st.checkbox("Select", value=checked_default, key=key)
                    if chk:
                        manual_select.append(e.get("webpage_url") or e.get("url") or e.get("id"))
            st.markdown("---")
            download_btn = st.button("⬇️ Download Selected Instagram Posts")
            if download_btn:
                if not manual_select:
                    st.warning("No posts selected. Use checkboxes or quick select.")
                else:
                    st.info(f"Downloading {len(manual_select)} selected items...")
                    files = download_with_progress(manual_select, audio=False, cookie=cookie)
                    if files:
                        for f in files:
                            with open(f, "rb") as fh:
                                st.download_button("⬇️ " + Path(f).name, data=fh, file_name=Path(f).name)

# COOKIE
elif page == "Cookie":
    st.markdown("<h2>⚙️ Instagram Cookie</h2>", unsafe_allow_html=True)
    st.markdown("If profile is private or blocked, paste cookie (single-line) to allow preview/downloads.")
    cookie_val = st.text_area("Paste full cookie string (sessionid=...; csrftoken=...; ...)", value=st.session_state.get("INSTAGRAM_COOKIE",""))
    if st.button("Save Cookie"):
        if cookie_val and cookie_val.strip():
            st.session_state["INSTAGRAM_COOKIE"] = cookie_val.strip()
            st.success("Cookie saved for this session.")
        else:
            st.warning("Paste a valid cookie string.")

# ABOUT
elif page == "About":
    st.markdown("<h2>💡 About</h2>", unsafe_allow_html=True)
    st.write("""
- Professional grid preview for TikTok & Instagram accounts  
- Choose specific posts with checkboxes or quickly select first N items  
- Auto-preview thumbnails & metadata for any pasted URL  
- Download MP4 or MP3 with live progress  
- Developer: Tanzeel ur Rehman
""")
    st.markdown("---")
    recent = sorted(list(OUT_DIR.glob("*")), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
    if recent:
        st.write("Recent downloads:")
        cols = st.columns(min(3, len(recent)))
        for i, f in enumerate(recent):
            with cols[i % len(cols)]:
                st.write(f.name)
                with open(f, "rb") as fh:
                    st.download_button("⬇️", data=fh, file_name=f.name)

st.markdown("</div>", unsafe_allow_html=True)
