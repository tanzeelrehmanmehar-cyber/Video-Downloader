import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import os
import time

# ---------- Page config ----------
st.set_page_config(
    page_title="🎬 Universal Downloader",
    page_icon="🎥",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------- Directories ----------
OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ---------- CSS (dark modern) ----------
st.markdown(
    """
<style>
body, .stApp { background: linear-gradient(180deg,#060607,#0c1016); color: #e6f7ff; font-family: 'Inter', sans-serif; }
h1, h2, h3 { color: #8ef0ff; text-align:center; }
.section { background: #0f1720; border-radius: 12px; padding: 18px; box-shadow: 0 6px 26px rgba(0,0,0,0.6); margin-bottom: 18px; }
.stButton>button { background: linear-gradient(90deg,#00e0ff,#0078ff); color: white; border-radius: 10px; padding: 8px 18px; font-weight:600; }
input[type=text], textarea { background:#11141a !important; color: #e6f7ff !important; border-radius:8px !important; padding: 10px !important; border: 1px solid #233042 !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#071018,#0f202a); color: white; }
footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Sidebar menu ----------
st.sidebar.title("🎬 Universal Downloader")
menu = st.sidebar.radio(
    "Choose an option",
    [
        "🏠 Home",
        "🎞️ Download Any Video (MP4)",
        "🎵 Download Audio (MP3)",
        "🎬 Download TikTok Account Videos",
        "📸 Download Instagram Account Videos",
        "⚙️ Set Instagram Cookie",
        "💡 About / Projects",
    ],
)

# session state for cookie and last file
if "INSTAGRAM_COOKIE" not in st.session_state:
    st.session_state["INSTAGRAM_COOKIE"] = ""

if "last_files" not in st.session_state:
    st.session_state["last_files"] = []

# ---------- Utility: human-friendly filename list display ----------
def show_downloaded_files(files):
    if not files:
        st.info("No files downloaded yet in this session.")
        return
    st.write("### ⤵️ Downloaded files (this session)")
    for p in files:
        p = Path(p)
        if p.exists():
            with open(p, "rb") as f:
                st.download_button(label=f"⬇️ {p.name}", data=f, file_name=p.name)

# ---------- Core downloader with progress hook ----------
def download_with_progress(url: str, *, audio_only: bool = False, cookie: str | None = None, out_dir: Path = OUT_DIR):
    """
    Download a single URL using yt-dlp and update Streamlit progress UI using a hook.
    Returns list of saved Path(s) or raises exception.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(out_dir / "%(title).100s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "nocheckcertificate": True,
        "noplaylist": False,   # allow playlist/profile downloads when URL is a profile/playlist
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "progress_hooks": [],
    }

    if audio_only:
        ydl_opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
    else:
        ydl_opts["format"] = "best"
        ydl_opts["merge_output_format"] = "mp4"

    if cookie:
        # write cookie string to temporary file for yt-dlp
        cookiefile = out_dir / "insta_cookie.txt"
        cookiefile.write_text(cookie)
        ydl_opts["cookiefile"] = str(cookiefile)

    # Prepare UI elements
    progress_bar = st.progress(0)
    status_text = st.empty()
    file_list_placeholder = st.empty()
    downloaded_paths = []

    def progress_hook(d):
        # called frequently with download status
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                pct = int(downloaded * 100 / total)
                progress_bar.progress(min(pct, 100))
                status_text.info(f"Downloading — {d.get('filename','file')} — {pct}% ({downloaded}/{total} bytes)")
            else:
                # unknown total
                progress_bar.progress(5)  # animate slight progress
                status_text.info(f"Downloading — {d.get('filename','file')} — {d.get('downloaded_bytes',0)} bytes")
        elif status == "finished":
            progress_bar.progress(100)
            status_text.success("Download finished — finalizing (merging/converting)...")
        elif status == "error":
            status_text.error("Error during download.")

    ydl_opts["progress_hooks"].append(progress_hook)

    # Run yt-dlp
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extract info first if we want to show metadata thumbnail/title (optional)
            # info = ydl.extract_info(url, download=False)
            # Then download (this also calls hooks)
            result = ydl.extract_info(url, download=True)
            # After download, find saved files in out_dir that are new or match pattern
            # yt-dlp can return dict or list
            saved = []
            if isinstance(result, dict):
                # single or playlist info
                # Try to build expected filename(s) using ydl.prepare_filename - simpler: scan folder for recent files
                # We'll pick files modified within last 60 seconds as downloaded candidates
                now = time.time()
                for p in out_dir.iterdir():
                    try:
                        if p.is_file() and (now - p.stat().st_mtime) < 300:  # 5 minutes window
                            saved.append(p)
                    except Exception:
                        continue
            elif isinstance(result, list):
                now = time.time()
                for p in out_dir.iterdir():
                    try:
                        if p.is_file() and (now - p.stat().st_mtime) < 300:
                            saved.append(p)
                    except Exception:
                        continue
            # Deduplicate and sort by mtime
            saved_unique = sorted(set(saved), key=lambda p: p.stat().st_mtime, reverse=True)
            for p in saved_unique:
                downloaded_paths.append(str(p))
    except Exception as e:
        progress_bar.empty()
        status_text.error(f"Download failed: {e}")
        raise

    # finalize UI
    if downloaded_paths:
        status_text.success("✅ Download complete!")
        file_list_placeholder.write("Saved files:")
        for p in downloaded_paths:
            file_list_placeholder.write(f"- `{p}`")
    else:
        status_text.warning("No files detected in download folder after yt-dlp finished.")

    return downloaded_paths

# ---------- Page handlers ----------
st.markdown("<div class='section'>", unsafe_allow_html=True)
if menu == "🏠 Home":
    st.markdown("<h1>🎥 Universal Downloader</h1>", unsafe_allow_html=True)
    st.write(
        "Use the sidebar to choose an option. This app uses **yt-dlp** under the hood and supports many sites (YouTube, TikTok, Instagram, etc.)."
    )
    st.write("Files are saved in the `downloads/` folder of the app container. Use the download buttons below to fetch files to your device.")
    show_downloaded_files(st.session_state["last_files"])

elif menu == "🎞️ Download Any Video (MP4)":
    st.markdown("<h2>🎞️ Download Any Video (MP4)</h2>", unsafe_allow_html=True)
    url = st.text_input("Paste video / reel URL (YouTube, TikTok, Instagram, etc.)", key="video_url")
    if st.button("Download Video (MP4)"):
        if not url or not url.strip():
            st.warning("Please paste a valid URL.")
        else:
            try:
                files = download_with_progress(url.strip(), audio_only=False, cookie=None)
                if files:
                    st.session_state["last_files"].extend(files)
                    show_downloaded_files(files)
            except Exception as e:
                st.error(f"Download error: {e}")

elif menu == "🎵 Download Audio (MP3)":
    st.markdown("<h2>🎵 Download Audio (MP3)</h2>", unsafe_allow_html=True)
    url = st.text_input("Paste video URL to extract MP3", key="audio_url")
    if st.button("Download Audio (MP3)"):
        if not url or not url.strip():
            st.warning("Please paste a valid URL.")
        else:
            try:
                files = download_with_progress(url.strip(), audio_only=True, cookie=None)
                if files:
                    st.session_state["last_files"].extend(files)
                    show_downloaded_files(files)
            except Exception as e:
                st.error(f"Download error: {e}")

elif menu == "🎬 Download TikTok Account Videos":
    st.markdown("<h2>🎬 Download TikTok Account Videos</h2>", unsafe_allow_html=True)
    t_username = st.text_input("Enter TikTok username (without @)", key="tiktok_user")
    t_count = st.number_input("Max videos to download (0 = all available)", min_value=0, max_value=500, value=0, step=1)
    if st.button("Download TikTok Account"):
        if not t_username or not t_username.strip():
            st.warning("Enter a TikTok username.")
        else:
            account_url = f"https://www.tiktok.com/@{t_username.strip()}"
            # yt-dlp will handle profile/playlist URLs; we pass the account_url and let it fetch all available videos
            try:
                files = download_with_progress(account_url, audio_only=False, cookie=None)
                if files:
                    # If user asked for limited count, trim by newest files
                    if t_count and t_count > 0:
                        files = files[: t_count]
                    st.session_state["last_files"].extend(files)
                    show_downloaded_files(files)
            except Exception as e:
                st.error(f"Download error: {e}")

elif menu == "📸 Download Instagram Account Videos":
    st.markdown("<h2>📸 Download Instagram Account Videos</h2>", unsafe_allow_html=True)
    ig_username = st.text_input("Enter Instagram username (without @)", key="ig_user")
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("Download Instagram Account"):
            if not ig_username or not ig_username.strip():
                st.warning("Enter an Instagram username.")
            else:
                profile_url = f"https://www.instagram.com/{ig_username.strip()}/"
                cookie = st.session_state.get("INSTAGRAM_COOKIE") or None
                try:
                    files = download_with_progress(profile_url, audio_only=False, cookie=cookie)
                    if files:
                        st.session_state["last_files"].extend(files)
                        show_downloaded_files(files)
                except Exception as e:
                    st.error(f"Download error: {e}")
    with btn_col2:
        st.info("If the account is private or Instagram blocks requests, set your Instagram cookie via 'Set Instagram Cookie' in the sidebar.")

elif menu == "⚙️ Set Instagram Cookie":
    st.markdown("<h2>⚙️ Set Instagram Cookie</h2>", unsafe_allow_html=True)
    st.markdown(
        "If you need to download from private accounts or avoid Instagram rate limiting, paste a full cookie string (single line, e.g. `sessionid=...; csrftoken=...;`)."
    )
    cookie_input = st.text_area("Paste full Instagram cookie string here", value=st.session_state["INSTAGRAM_COOKIE"])
    if st.button("Save Cookie"):
        if cookie_input and cookie_input.strip():
            st.session_state["INSTAGRAM_COOKIE"] = cookie_input.strip()
            st.success("✅ Instagram cookie saved in session (will be used for Instagram downloads).")
        else:
            st.warning("Paste a non-empty cookie string.")

elif menu == "💡 About / Projects":
    st.markdown("<h2>💡 About & Projects</h2>", unsafe_allow_html=True)
    st.write(
        """
- Built with **Streamlit** + **yt-dlp**  
- Supports downloads from many sites (YouTube, TikTok, Instagram, Reels, etc.)  
- Developer: **Tanzeel ur Rehman**
"""
    )
    st.markdown("---")
    show_downloaded_files(st.session_state["last_files"])

st.markdown("</div>", unsafe_allow_html=True)
