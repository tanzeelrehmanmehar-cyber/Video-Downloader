‎# app.py
‎import streamlit as st
‎from yt_dlp import YoutubeDL
‎from pathlib import Path
‎import threading
‎import time
‎import shutil
‎import tempfile
‎import traceback
‎import streamlit.components.v1 as components
‎from typing import List, Optional
‎import os
‎
‎# --------- App branding ----------
‎APP_TITLE = "All Video Downloader"
‎APP_TAGLINE = "Enjoy"
‎HOME_HTML = "home.html"  # must be in same folder
‎
‎# --------- Page config ----------
‎st.set_page_config(
‎    page_title=f"{APP_TITLE} — {APP_TAGLINE}",
‎    page_icon="🎬",
‎    layout="wide",
‎    initial_sidebar_state="expanded",
‎)
‎
‎# --------- Folders ----------
‎OUT_DIR = Path("downloads")
‎OUT_DIR.mkdir(exist_ok=True)
‎
‎# --------- CSS (dark - neon) ----------
‎st.markdown(
‎    """
‎<style>
‎/* App theme */
‎body, .stApp { background: linear-gradient(180deg,#030407,#07101a); color: #eafcff; font-family: Inter, sans-serif; }
‎h1,h2,h3 { text-align:center; color:#8ef0ff; }
‎
‎/* Card */
‎.card { background: linear-gradient(180deg,#07121a,#08121a); border-radius:14px; padding:14px; margin:10px; box-shadow: 0 14px 46px rgba(0,0,0,0.7); border:1px solid rgba(0,140,255,0.06); }
‎
‎/* Buttons */
‎.stButton>button { background: linear-gradient(90deg,#00c2ff,#0069ff); color: white; font-weight:700; border-radius:10px; padding:10px 18px; width:100%; box-shadow:0 8px 20px rgba(0,100,255,0.18); }
‎.stButton>button:hover { transform: translateY(-3px); }
‎
‎/* Inputs */
‎input[type=text], textarea { background:#07111a !important; color:#eafcff !important; border-radius:8px !important; padding:10px !important; border:1px solid #183045 !important; }
‎
‎/* Grid */
‎.grid { display:flex; flex-wrap:wrap; gap:14px; justify-content:center; margin-top:12px; }
‎.grid-item { width:300px; background: linear-gradient(180deg,#08121a,#0b1720); border-radius:12px; padding:8px; box-shadow:0 10px 30px rgba(0,0,0,0.6); transition: transform .18s ease, box-shadow .18s ease; border:1px solid rgba(0,120,255,0.04); }
‎.grid-item:hover { transform: translateY(-6px); box-shadow: 0 18px 40px rgba(0,140,255,0.12); }
‎.grid-thumb { width:100%; height:170px; object-fit:cover; border-radius:8px; transition: transform .22s ease, box-shadow .22s ease; }
‎.grid-item:hover .grid-thumb { transform: scale(1.06); box-shadow: 0 10px 30px rgba(0,200,255,0.14); }
‎.grid-title { font-weight:700; font-size:14px; margin-top:8px; color:#eafcff; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
‎.grid-meta { color:#98e9ff88; font-size:12px; margin-top:6px; }
‎.chk-row { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:8px; }
‎
‎/* responsive */
‎@media (max-width: 950px) { .grid-item { width:100%; } }

/* Hide Streamlit header, footer & hamburger menu */
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden !important;}
[data-testid="stHeader"] {display: none;}
#MainMenu {visibility: hidden;}


‎/* hide default footer */
‎footer { display:none !important; }
‎</style>
‎""",
‎    unsafe_allow_html=True,
‎)
‎
‎# --------- Sidebar buttons that auto-close ----------
‎if "page" not in st.session_state:
‎    st.session_state.page = "Home"
‎if "INSTAGRAM_COOKIE" not in st.session_state:
‎    st.session_state.INSTAGRAM_COOKIE = ""
‎if "preview_cache" not in st.session_state:
‎    st.session_state.preview_cache = {}
‎if "download_thread" not in st.session_state:
‎    st.session_state.download_thread = None
‎
‎def set_page_and_close(page_name: str):
‎    st.session_state.page = page_name
‎    # JS to click Streamlit sidebar toggle button (collapses sidebar)
‎    js = """
‎    <script>
‎    (function(){
‎      const sbToggle = window.parent.document.querySelector('button[aria-label="Toggle sidebar"]');
‎      if (sbToggle) { sbToggle.click(); }
‎    })();
‎    </script>
‎    """
‎    components.html(js, height=0)
‎
‎with st.sidebar:
‎    st.markdown(f"## 🎬 {APP_TITLE}")
‎    st.markdown("---")
‎    if st.button("🏠 Home", on_click=set_page_and_close, args=("Home",)): pass
‎    if st.button("🔎 Any Video (MP4)", on_click=set_page_and_close, args=("AnyVideo",)): pass
‎    if st.button("🎧 Audio (MP3)", on_click=set_page_and_close, args=("Audio",)): pass
‎    if st.button("🎬 TikTok Account", on_click=set_page_and_close, args=("TikTok",)): pass
‎    if st.button("📸 Instagram Account", on_click=set_page_and_close, args=("Instagram",)): pass
‎    if st.button("⚙️ Set Instagram Cookie", on_click=set_page_and_close, args=("Cookie",)): pass
‎    if st.button("💡 About", on_click=set_page_and_close, args=("About",)): pass
‎
‎# floating open menu button if user collapsed sidebar
‎open_menu_html = """
‎<button id="openMenuBtn" style="position:fixed;left:12px;top:12px;padding:8px 12px;border-radius:8px;border:none;background:linear-gradient(90deg,#00c2ff,#0069ff);color:#001;font-weight:700;z-index:9999;display:none;"
‎ onclick="
‎  try{
‎    const sbToggle = window.parent.document.querySelector('button[aria-label=\"Toggle sidebar\"]');
‎    if (sbToggle) sbToggle.click();
‎    this.style.display='none';
‎  }catch(e){console.log(e)}
‎">☰ Menu</button>
‎<script>
‎(function(){
‎  setTimeout(function(){
‎    const sb = window.parent.document.querySelector('[data-testid=\"stSidebar\"]');
‎    const openBtn = document.getElementById('openMenuBtn');
‎    if (sb && openBtn){
‎      const style = window.getComputedStyle(sb);
‎      if (style && style.display === 'none'){ openBtn.style.display='block'; }
‎    }
‎  }, 700);
‎})();
‎</script>
‎"""
‎components.html(open_menu_html, height=0)
‎
‎# --------- Utility functions ----------
‎def human_duration(seconds: Optional[int]) -> str:
‎    try:
‎        s = int(seconds or 0)
‎        m = s // 60
‎        sec = s % 60
‎        return f"{m}:{sec:02d}"
‎    except Exception:
‎        return str(seconds or "")
‎
‎def fetch_metadata(url: str, cookie: Optional[str] = None, limit_preview: int = 24):
‎    """Uses yt-dlp to extract metadata (no download). Caches results."""
‎    cache_key = f"{url}::cookie={bool(cookie)}::limit={limit_preview}"
‎    if cache_key in st.session_state.preview_cache:
‎        return st.session_state.preview_cache[cache_key]
‎    opts = {"quiet": True, "no_warnings": True}
‎    if cookie:
‎        tmp = OUT_DIR / "preview_cookie.txt"
‎        tmp.write_text(cookie)
‎        opts["cookiefile"] = str(tmp)
‎    try:
‎        with YoutubeDL(opts) as ydl:
‎            info = ydl.extract_info(url, download=False)
‎            if isinstance(info, dict) and "entries" in info:
‎                entries = [e for e in info["entries"] if isinstance(e, dict)]
‎                info_preview = dict(info)
‎                info_preview["entries"] = entries[:limit_preview]
‎                st.session_state.preview_cache[cache_key] = info_preview
‎                return info_preview
‎            st.session_state.preview_cache[cache_key] = info
‎            return info
‎    except Exception as e:
‎        st.error(f"Preview failed: {e}")
‎        return None
‎
‎def _yt_download_worker(ydl_opts, urls: List[str], result_paths: List[str], audio=False, cookie=None, playlist_end=None):
‎    """
‎    Run yt-dlp downloads sequentially in background thread.
‎    This worker writes found files into result_paths list.
‎    """
‎    try:
‎        with YoutubeDL(ydl_opts) as ydl:
‎            if len(urls) == 1 and (urls[0].startswith("https://www.tiktok.com/") or urls[0].startswith("https://www.instagram.com/")):
‎                # profile/playlist URL
‎                if playlist_end and isinstance(playlist_end, int) and playlist_end > 0:
‎                    ydl.params["playlistend"] = playlist_end
‎                res = ydl.extract_info(urls[0], download=True)
‎            else:
‎                for u in urls:
‎                    ydl.extract_info(u, download=True)
‎        # find recent files (last 15 minutes)
‎        now = time.time()
‎        for p in OUT_DIR.iterdir():
‎            try:
‎                if p.is_file() and (now - p.stat().st_mtime) < 900:
‎                    result_paths.append(str(p))
‎            except Exception:
‎                continue
‎    except Exception as e:
‎        result_paths.append(f"__ERROR__:{e}")
‎
‎def download_with_animation(urls: List[str], audio: bool = False, cookie: Optional[str] = None, playlist_end: Optional[int] = None) -> List[str]:
‎    """
‎    Starts a background download and shows an animated progress bar in the UI while it runs.
‎    Returns list of downloaded file paths (or empty on failure).
‎    """
‎    outtmpl = str(OUT_DIR / "%(title).100s.%(ext)s")
‎    ydl_opts = {
‎        "outtmpl": outtmpl,
‎        "quiet": True,
‎        "no_warnings": True,
‎        "ignoreerrors": True,
‎        # progress_hooks not used for percentage accuracy (we animate instead)
‎    }
‎    if audio:
‎        ydl_opts.update({
‎            "format": "bestaudio/best",
‎            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
‎        })
‎    else:
‎        ydl_opts.update({"format": "best", "merge_output_format": "mp4"})
‎
‎    if cookie:
‎        cf = OUT_DIR / "dl_cookie.txt"
‎        cf.write_text(cookie)
‎        ydl_opts["cookiefile"] = str(cf)
‎
‎    result_paths: List[str] = []
‎    # spawn thread
‎    worker = threading.Thread(target=_yt_download_worker, args=(ydl_opts, urls, result_paths, audio, cookie, playlist_end))
‎    worker.start()
‎    st.session_state.download_thread = worker
‎
‎    # animated progress while thread alive
‎    progress = st.progress(0)
‎    status = st.empty()
‎    t = 0
‎    while worker.is_alive():
‎        # animate a looping bar (0..100)
‎        t = (t + 7) % 100
‎        progress.progress(t)
‎        status.info("Downloading... (this is an animated progress bar)")
‎        time.sleep(0.18)
‎    # finished
‎    progress.progress(100)
‎    status.success("Download finished — finalizing files...")
‎    # small wait for filesystem updates
‎    time.sleep(0.6)
‎
‎    # collect results (filter out errors)
‎    downloaded = [p for p in result_paths if not p.startswith("__ERROR__")]
‎    errors = [p for p in result_paths if p.startswith("__ERROR__")]
‎    if errors:
‎        status.error("Some downloads failed. See logs.")
‎        for e in errors:
‎            st.text(e)
‎    return downloaded
‎
‎# --------- UI pages ----------
‎st.markdown("<div class='card'>", unsafe_allow_html=True)
‎page = st.session_state.page
‎
‎# HOME: embed home.html but theme applied
‎if page == "Home":
‎    st.markdown(f"<h1>🎬 {APP_TITLE}</h1>", unsafe_allow_html=True)
‎    st.markdown(f"<h4>{APP_TAGLINE}</h4>", unsafe_allow_html=True)
‎    st.markdown("---")
‎    if Path(HOME_HTML).exists():
‎        try:
‎            html_content = Path(HOME_HTML).read_text(encoding="utf-8")
‎            wrapped = f"<div style='padding:8px;background:transparent;border-radius:8px'>{html_content}</div>"
‎            st.components.v1.html(wrapped, height=560, scrolling=True)
‎        except Exception as e:
‎            st.error("Failed to load home.html")
‎            st.text(str(e))
‎    else:
‎        st.info(f"Place a '{HOME_HTML}' file in the app folder to show your landing page here.")
‎    st.markdown("---")
‎    recent = sorted(list(OUT_DIR.glob("*")), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
‎    if recent:
‎        st.write("Recent downloads (click to save):")
‎        cols = st.columns(min(3, len(recent)))
‎        for i, f in enumerate(recent):
‎            with cols[i % len(cols)]:
‎                st.write(f.name)
‎                with open(f, "rb") as fh:
‎                    st.download_button("⬇️ Save", data=fh, file_name=f.name)
‎    else:
‎        st.info("No downloads yet.")
‎
‎# ANY VIDEO (MP4): auto-preview + download
‎elif page == "AnyVideo":
‎    st.markdown("<h2>🎞️ Download Any Video (MP4)</h2>", unsafe_allow_html=True)
‎    url = st.text_input("Paste video / reel URL", key="any_video_url")
‎    if url and url.strip():
‎        with st.spinner("Fetching preview..."):
‎            info = fetch_metadata(url.strip(), limit_preview=1)
‎        if info:
‎            entry = info["entries"][0] if isinstance(info, dict) and "entries" in info else info
‎            title = entry.get("title", "No title")
‎            thumbnail = entry.get("thumbnail")
‎            uploader = entry.get("uploader") or entry.get("uploader_id", "")
‎            duration = human_duration(entry.get("duration"))
‎            c1, c2 = st.columns([1, 2])
‎            with c1:
‎                if thumbnail:
‎                    st.image(thumbnail, use_column_width=True)
‎            with c2:
‎                st.markdown(f"**{title}**")
‎                st.write(f"Uploader: {uploader}")
‎                st.write(f"Duration: {duration}")
‎            st.markdown("---")
‎            if st.button("⬇️ Download MP4"):
‎                downloaded = download_with_animation([url.strip()], audio=False)
‎                if downloaded:
‎                    st.success(f"Downloaded {len(downloaded)} file(s).")
‎                    for p in downloaded:
‎                        with open(p, "rb") as fh:
‎                            st.download_button("⬇️ Save file", data=fh, file_name=Path(p).name)
‎
‎# AUDIO (MP3)
‎elif page == "Audio":
‎    st.markdown("<h2>🎧 Extract Audio (MP3)</h2>", unsafe_allow_html=True)
‎    url = st.text_input("Paste video URL to extract audio", key="audio_url")
‎    if url and url.strip():
‎        with st.spinner("Fetching preview..."):
‎            info = fetch_metadata(url.strip(), limit_preview=1)
‎        if info:
‎            entry = info["entries"][0] if isinstance(info, dict) and "entries" in info else info
‎            st.markdown(f"**{entry.get('title','No title')}**")
‎            if entry.get("thumbnail"):
‎                st.image(entry.get("thumbnail"), width=360)
‎            st.write(f"Uploader: {entry.get('uploader') or ''}")
‎        if st.button("⬇️ Download MP3"):
‎            downloaded = download_with_animation([url.strip()], audio=True)
‎            if downloaded:
‎                st.success("Audio downloaded.")
‎                for p in downloaded:
‎                    with open(p, "rb") as fh:
‎                        st.download_button("⬇️ Save audio", data=fh, file_name=Path(p).name)
‎
‎# TIKTOK Account: grid preview, select/deselect visible, quick select N, ZIP download
‎elif page == "TikTok":
‎    st.markdown("<h2>🎬 TikTok Account — Grid Preview</h2>", unsafe_allow_html=True)
‎    username = st.text_input("Enter TikTok username (without @)", key="tt_user")
‎    if username and username.strip():
‎        account_url = f"https://www.tiktok.com/@{username.strip()}"
‎        preview_limit = st.slider("Preview first N videos", 3, 36, 12, 3, key="tt_preview")
‎        with st.spinner("Fetching preview..."):
‎            info = fetch_metadata(account_url, limit_preview=preview_limit)
‎        entries = info.get("entries") if info and isinstance(info, dict) else None
‎        if not entries:
‎            st.info("No preview available — account may be private or blocked. Try cookie.")
‎        else:
‎            st.write(f"Showing {len(entries)} items from @{username.strip()}")
‎            c1, c2, c3 = st.columns([1,1,2])
‎            with c1:
‎                if st.button("Select All Visible (TikTok)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"tt_chk_{idx}"] = True
‎                    st.experimental_rerun()
‎            with c2:
‎                if st.button("Deselect All Visible (TikTok)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"tt_chk_{idx}"] = False
‎                    st.experimental_rerun()
‎            with c3:
‎                select_first = st.number_input("Quick select first N", min_value=0, max_value=len(entries), value=0, step=1, key="tt_quick")
‎                if st.button("Apply Quick Select (TikTok)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"tt_chk_{idx}"] = True if idx < select_first else False
‎                    st.experimental_rerun()
‎
‎            st.markdown("<div class='grid'>", unsafe_allow_html=True)
‎            selected_urls = []
‎            for idx, e in enumerate(entries):
‎                url_item = e.get("webpage_url") or e.get("url") or e.get("id")
‎                key = f"tt_chk_{idx}"
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
‎            if st.button("⬇️ Download Selected & Create ZIP (TikTok)"):
‎                if not selected_urls:
‎                    st.warning("No items selected.")
‎                else:
‎                    st.info(f"Downloading {len(selected_urls)} selected items...")
‎                    files = download_with_animation(selected_urls, audio=False)
‎                    if files:
‎                        # create zip of selected files
‎                        tmp_dir = OUT_DIR / f"tmp_zip_{int(time.time())}"
‎                        tmp_dir.mkdir(exist_ok=True)
‎                        for f in files:
‎                            src = Path(f)
‎                            if src.exists():
‎                                shutil.copy(src, tmp_dir / src.name)
‎                        zip_name = OUT_DIR / f"{username.strip()}_selected_{int(time.time())}.zip"
‎                        shutil.make_archive(str(zip_name.with_suffix('')), 'zip', root_dir=tmp_dir)
‎                        shutil.rmtree(tmp_dir)
‎                        st.success(f"ZIP created: {zip_name.name}")
‎                        with open(zip_name, "rb") as zf:
‎                            st.download_button("⬇️ Download ZIP", data=zf, file_name=zip_name.name)
‎
‎# INSTAGRAM Account: grid preview + selection + ZIP (cookie support)
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
‎            st.info("No preview entries found. Profile may be private or blocked. Set cookie in Cookie page.")
‎        else:
‎            st.write(f"Showing {len(entries)} items from @{ig_user.strip()}")
‎            c1, c2, c3 = st.columns([1,1,2])
‎            with c1:
‎                if st.button("Select All Visible (IG)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"ig_chk_{idx}"] = True
‎                    st.experimental_rerun()
‎            with c2:
‎                if st.button("Deselect All Visible (IG)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"ig_chk_{idx}"] = False
‎                    st.experimental_rerun()
‎            with c3:
‎                select_first = st.number_input("Quick select first N", min_value=0, max_value=len(entries), value=0, step=1, key="ig_quick")
‎                if st.button("Apply Quick Select (IG)"):
‎                    for idx in range(len(entries)):
‎                        st.session_state[f"ig_chk_{idx}"] = True if idx < select_first else False
‎                    st.experimental_rerun()
‎
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
‎                    files = download_with_animation(selected_urls, audio=False, cookie=cookie)
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
‎    st.markdown("If profile preview fails or profile is private, paste cookie string (single-line): sessionid=...; csrftoken=...;")
‎    cookie_val = st.text_area("Paste cookie (session only)", value=st.session_state.INSTAGRAM_COOKIE, height=140)
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
‎- Professional grid preview with thumbnail hover and select/deselect all visible.  
‎- ZIP creation of selected items and single-button download.  
‎- Auto-close sidebar for mobile friendliness.  
‎- Built with Streamlit + yt-dlp.  
‎- Developer: Tanzeel ur Rehman
‎""")
‎    st.markdown("---")
‎    recent = sorted(list(OUT_DIR.glob("*")), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
‎    if recent:
‎        st.write("Recent files:")
‎        cols = st.columns(min(3, len(recent)))
‎        for i, f in enumerate(recent):
‎            with cols[i % len(cols)]:
‎                st.write(f.name)
‎                with open(f, "rb") as fh:
‎                    st.download_button("⬇️ Save", data=fh, file_name=f.name)
‎
‎st.markdown("</div>", unsafe_allow_html=True)
