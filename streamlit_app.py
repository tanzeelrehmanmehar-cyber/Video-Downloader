# app.py
import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import time
import traceback
import streamlit.components.v1 as components

# ---------- Config ----------
st.set_page_config(
    page_title="Universal Downloader (Pro)",
    page_icon="🎥",
    layout="centered",
    initial_sidebar_state="expanded",
)

OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ---------- Styles ----------
st.markdown(
    """
<style>
/* Dark theme + centered card look */
body, .stApp { background: linear-gradient(180deg,#060607,#0c1016); color: #eefcff; font-family: Inter, sans-serif; }
.section { background: #0f1720; border-radius: 12px; padding: 18px; box-shadow: 0 8px 30px rgba(0,0,0,0.6); margin-bottom: 18px; width: min(94%,820px); }
h1, h2, h3 { color:#9ef0ff; text-align:center; }
.stButton>button { background: linear-gradient(90deg,#00e0ff,#0078ff); color: white; border-radius: 10px; padding: 8px 18px; font-weight:600; }
input[type=text], textarea { background:#0b0f14 !important; color: #eefcff !important; border-radius:10px !important; padding:10px !important; border:1px solid #233042 !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#071018,#0f202a); color: white; }
#openMenuBtn { position: fixed; top: 12px; left: 12px; z-index: 9999; display: none; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Sidebar menu ----------
st.sidebar.title("🎬 Universal Downloader (Pro)")
menu = st.sidebar.radio(
    "Choose",
    [
        "🏠 Home",
        "🎞️ Any Video (MP4)",
        "🎵 Audio (MP3)",
        "🎬 TikTok Account",
        "📸 Instagram Account",
        "⚙️ Set Instagram Cookie",
        "💡 About",
    ],
)

# Hide sidebar automatically when menu changes (run JS once per change)
if "menu_prev" not in st.session_state:
    st.session_state.menu_prev = None

if st.session_state.menu_prev != menu:
    # Run JS to hide sidebar and show an 'Open menu' floating button
    hide_js = """
    <script>
    const hideSidebar = () => {
      try {
        const sb = document.querySelector('[data-testid="stSidebar"]');
        if (sb) sb.style.display = 'none';
        const menuBtn = document.querySelector('button[aria-label="Toggle sidebar"]');
        if (menuBtn) menuBtn.style.display = 'none';
        const openBtn = document.getElementById('openMenuBtn');
        if (openBtn) openBtn.style.display = 'block';
      } catch(e) {console.log(e)}
    };
    hideSidebar();
    </script>
    """
    components.html(hide_js, height=0)
    st.session_state.menu_prev = menu

# Provide floating open-menu button (reopens sidebar)
open_menu_html = """
<style>#openMenuBtn{background: linear-gradient(90deg,#00e0ff,#0078ff); color:#001; border:none; padding:8px 12px; border-radius:8px; font-weight:700; cursor:pointer; box-shadow:0 6px 20px rgba(0,120,255,0.25);}</style>
<button id="openMenuBtn" onclick="
  try{
    const sb = document.querySelector('[data-testid=\"stSidebar\"]');
    if (sb) sb.style.display = 'block';
    const menuBtn = document.querySelector('button[aria-label=\"Toggle sidebar\"]');
    if (menuBtn) menuBtn.style.display = '';
    this.style.display='none';
  }catch(e){console.log(e)}
" title="Open menu">☰ Menu</button>
"""
components.html(open_menu_html, height=40)

# ---------- Session state ----------
if "INSTAGRAM_COOKIE" not in st.session_state:
    st.session_state["INSTAGRAM_COOKIE"] = ""
if "last_files" not in st.session_state:
    st.session_state["last_files"] = []

# ---------- Utility functions ----------
def show_download_buttons(paths):
    """Show download_button for each path (Streamlit)"""
    for p in paths:
        p = Path(p)
        if p.exists():
            with open(p, "rb") as f:
                st.download_button(label=f"⬇️ {p.name}", data=f, file_name=p.name)

def extract_info(url, cookie: str | None = None, n_preview:int|None=None):
    """Use yt-dlp to extract metadata (no download)"""
    opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True}
    if cookie:
        # write cookie temporarily and point cookiefile
        tmp = OUT_DIR / "insta_cookie_preview.txt"
        tmp.write_text(cookie)
        opts["cookiefile"] = str(tmp)
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # If 'entries' (playlist/profile), optionally crop to n_preview
            if isinstance(info, dict) and "entries" in info:
                entries = [e for e in info["entries"] if isinstance(e, dict)]
                if n_preview and n_preview > 0:
                    entries = entries[:n_preview]
                info_preview = {**info}
                info_preview["entries"] = entries
                return info_preview
            return info
    except Exception as e:
        st.error(f"Preview failed: {e}")
        return None

# Core downloader with progress hooks
def download_with_progress(url: str, audio_only: bool=False, cookie: str|None=None, out_dir: Path = OUT_DIR, playlist_end: int | None = None):
    out_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(out_dir / "%(title).100s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "nocheckcertificate": True,
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "progress_hooks": []
    }
    if playlist_end and isinstance(playlist_end,int) and playlist_end>0:
        ydl_opts["playlistend"] = playlist_end

    if audio_only:
        ydl_opts.update({
            "format":"bestaudio/best",
            "postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
        })
    else:
        ydl_opts["format"] = "best"
        ydl_opts["merge_output_format"] = "mp4"

    if cookie:
        cookiefile = out_dir / "insta_cookie.txt"
        cookiefile.write_text(cookie)
        ydl_opts["cookiefile"] = str(cookiefile)

    progress_bar = st.progress(0)
    status = st.empty()
    downloaded_paths = []

    def hook(d):
        s = d.get("status")
        if s == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                pct = int(downloaded * 100 / total)
                progress_bar.progress(min(pct, 100))
                status.info(f"Downloading: {d.get('filename','file')} — {pct}%")
            else:
                progress_bar.progress(5)
                status.info(f"Downloading... {downloaded} bytes")
        elif s == "finished":
            progress_bar.progress(100)
            status.success("Finished. Finalizing...")
        elif s == "error":
            status.error("Error during download.")

    ydl_opts["progress_hooks"].append(hook)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=True)
            # find recently-modified files in out_dir (5 minutes window)
            now = time.time()
            saved = []
            for p in out_dir.iterdir():
                try:
                    if p.is_file() and (now - p.stat().st_mtime) < 300:
                        saved.append(p)
                except Exception:
                    continue
            saved_sorted = sorted(set(saved), key=lambda p: p.stat().st_mtime, reverse=True)
            downloaded_paths = [str(p) for p in saved_sorted]
            if downloaded_paths:
                status.success("✅ Download complete!")
            else:
                status.warning("No files detected after download finished.")
            progress_bar.empty()
            return downloaded_paths
    except Exception as e:
        progress_bar.empty()
        st.error(f"Download failed: {e}")
        st.error(traceback.format_exc())
        return []

# ---------- UI pages ----------
st.markdown("<div class='section'>", unsafe_allow_html=True)

if menu == "🏠 Home":
    st.markdown("<h1>🎥 Universal Downloader (Pro)</h1>", unsafe_allow_html=True)
    st.write("Paste a video URL into any page — the app will show an automatic preview (thumbnail, title, duration). Use the sidebar to pick features.")
    st.write("Files saved into `downloads/` (container). Download buttons below fetch them to your device.")
    if st.session_state["last_files"]:
        st.write("### Recent downloads (this session)")
        show_download_buttons(st.session_state["last_files"])
    else:
        st.info("No downloads yet this session. Select an option from the sidebar to begin.")

# ---------------- Any Video (MP4) ----------------
elif menu == "🎞️ Any Video (MP4)":
    st.markdown("<h2>🎞️ Download Any Video (MP4)</h2>", unsafe_allow_html=True)
    url = st.text_input("Paste video URL (YouTube, TikTok, Instagram, etc.)", key="any_url")
    # auto-preview on input (A)
    if url and url.strip():
        with st.spinner("Fetching preview..."):
            info = extract_info(url.strip(), cookie=None, n_preview=1)
        if info:
            if isinstance(info, dict) and "entries" in info:
                st.write("**Playlist / Profile detected — previewing first items:**")
                entries = info.get("entries") or []
                for idx, e in enumerate(entries, start=1):
                    if not e: continue
                    st.markdown(f"**{idx}. {e.get('title','(no title)')}** — {e.get('uploader') or e.get('uploader_id') or ''}")
                    thumb = e.get("thumbnail")
                    if thumb:
                        st.image(thumb, width=320)
                    dur = e.get("duration")
                    if dur:
                        st.caption(f"Duration: {dur} seconds")
            else:
                st.markdown(f"**{info.get('title','(no title)')}**")
                st.write(f"Uploader: {info.get('uploader') or info.get('uploader_id','')}")
                dur = info.get("duration")
                if dur:
                    minutes = int(dur // 60)
                    seconds = int(dur % 60)
                    st.caption(f"Duration: {minutes}:{seconds:02d}")
                thumb = info.get("thumbnail")
                if thumb:
                    st.image(thumb, width=360)
    if st.button("Download MP4"):
        if not url or not url.strip():
            st.warning("Paste a valid URL first.")
        else:
            files = download_with_progress(url.strip(), audio_only=False, cookie=None)
            if files:
                st.session_state["last_files"].extend(files)
                show_download_buttons(files)

# ---------------- Audio (MP3) ----------------
elif menu == "🎵 Audio (MP3)":
    st.markdown("<h2>🎵 Extract Audio (MP3)</h2>", unsafe_allow_html=True)
    url = st.text_input("Paste video URL to extract MP3", key="audio_url")
    if url and url.strip():
        with st.spinner("Fetching preview..."):
            info = extract_info(url.strip(), cookie=None, n_preview=1)
        if info and not isinstance(info, dict) or (isinstance(info, dict) and "entries" not in info):
            st.markdown(f"**{info.get('title','(no title)')}**")
            st.write(f"Uploader: {info.get('uploader') or info.get('uploader_id','')}")
            if info.get("thumbnail"):
                st.image(info.get("thumbnail"), width=320)
    if st.button("Download MP3"):
        if not url or not url.strip():
            st.warning("Paste a valid URL first.")
        else:
            files = download_with_progress(url.strip(), audio_only=True, cookie=None)
            if files:
                st.session_state["last_files"].extend(files)
                show_download_buttons(files)

# ---------------- TikTok Account ----------------
elif menu == "🎬 TikTok Account":
    st.markdown("<h2>🎬 TikTok Account Videos</h2>", unsafe_allow_html=True)
    username = st.text_input("TikTok username (without @)", key="tiktok_user")
    max_v = st.number_input("Max videos to download (0 = all available)", min_value=0, max_value=500, value=0, step=1)
    preview_count = st.slider("Preview first N videos", min_value=1, max_value=20, value=6)
    if username and username.strip():
        account_url = f"https://www.tiktok.com/@{username.strip()}"
        # auto-preview first N entries
        with st.spinner("Fetching account preview..."):
            info = extract_info(account_url, cookie=None, n_preview=preview_count)
        if info and isinstance(info, dict) and info.get("entries"):
            st.write(f"Previewing first {len(info['entries'])} videos from @{username.strip()}")
            for e in info["entries"]:
                if not e: continue
                st.markdown(f"**{e.get('title','(no title)')}** — {e.get('uploader') or ''}")
                if e.get("thumbnail"):
                    st.image(e.get("thumbnail"), width=280)
        else:
            st.info("No preview entries (site may block profile listing or profile is private).")
    if st.button("Download TikTok Account Videos"):
        if not username or not username.strip():
            st.warning("Enter a TikTok username.")
        else:
            account_url = f"https://www.tiktok.com/@{username.strip()}"
            files = download_with_progress(account_url, audio_only=False, cookie=None, out_dir=OUT_DIR, playlist_end=(None if max_v==0 else int(max_v)))
            if files:
                if max_v and max_v>0:
                    files = files[:max_v]
                st.session_state["last_files"].extend(files)
                show_download_buttons(files)

# ---------------- Instagram Account ----------------
elif menu == "📸 Instagram Account":
    st.markdown("<h2>📸 Instagram Account Videos</h2>", unsafe_allow_html=True)
    ig_user = st.text_input("Instagram username (without @)", key="ig_user")
    max_v = st.number_input("Max videos to download (0 = all available)", min_value=0, max_value=500, value=0, step=1)
    preview_count = st.slider("Preview first N posts", min_value=1, max_value=20, value=6, key="ig_preview_count")
    if ig_user and ig_user.strip():
        profile_url = f"https://www.instagram.com/{ig_user.strip()}/"
        cookie = st.session_state.get("INSTAGRAM_COOKIE") or None
        with st.spinner("Fetching preview (may require cookie for private accounts)..."):
            info = extract_info(profile_url, cookie=cookie, n_preview=preview_count)
        if info and isinstance(info, dict) and info.get("entries"):
            st.write(f"Previewing first {len(info['entries'])} posts from @{ig_user.strip()}")
            for e in info["entries"]:
                if not e: continue
                st.markdown(f"**{e.get('title','(no title)')}** — {e.get('uploader') or ''}")
                if e.get("thumbnail"):
                    st.image(e.get("thumbnail"), width=280)
        else:
            st.info("No preview entries (private account or Instagram blocking). Try setting cookie in sidebar.")
    if st.button("Download Instagram Account Videos"):
        if not ig_user or not ig_user.strip():
            st.warning("Enter an Instagram username.")
        else:
            profile_url = f"https://www.instagram.com/{ig_user.strip()}/"
            cookie = st.session_state.get("INSTAGRAM_COOKIE") or None
            files = download_with_progress(profile_url, audio_only=False, cookie=cookie, out_dir=OUT_DIR, playlist_end=(None if max_v==0 else int(max_v)))
            if files:
                if max_v and max_v>0:
                    files = files[:max_v]
                st.session_state["last_files"].extend(files)
                show_download_buttons(files)

# ---------------- Cookie settings ----------------
elif menu == "⚙️ Set Instagram Cookie":
    st.markdown("<h2>⚙️ Instagram Cookie (optional)</h2>", unsafe_allow_html=True)
    st.markdown("If an Instagram profile is private or your requests are being blocked, paste your full cookie string (single line) here. Keep it private.")
    cookie = st.text_area("Paste cookie (sessionid=...; csrftoken=...; ...)", value=st.session_state.get("INSTAGRAM_COOKIE",""))
    if st.button("Save Cookie"):
        if cookie and cookie.strip():
            st.session_state["INSTAGRAM_COOKIE"] = cookie.strip()
            st.success("✅ Cookie saved to session.")
        else:
            st.warning("Paste a non-empty cookie string.")

# ---------------- About ----------------
elif menu == "💡 About":
    st.markdown("<h2>💡 About</h2>", unsafe_allow_html=True)
    st.write(
        """
- Built with **Streamlit + yt-dlp**  
- Auto-preview on URL input (thumbnail, title, duration)  
- Limit account downloads and preview first N items  
- Sidebar auto-closes for a mobile-first experience; use the ☰ Menu button to re-open
- Developer: Tanzeel ur Rehman
"""
    )
    if st.session_state["last_files"]:
        st.markdown("---")
        st.write("### Recent downloads (this session)")
        show_download_buttons(st.session_state["last_files"])

st.markdown("</div>", unsafe_allow_html=True)
