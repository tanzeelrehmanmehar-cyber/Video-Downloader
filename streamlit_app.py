import streamlit as st
import streamlit.components.v1 as components
from yt_dlp import YoutubeDL
import os, zipfile, tempfile, time
from pathlib import Path

# -------------------- CONFIG --------------------
st.set_page_config(page_title="TechHelp Downloader", page_icon="🎬", layout="wide")
st.markdown("""
<style>
header, footer {visibility: hidden;}
.stApp { background: linear-gradient(180deg,#020611,#041826); color: #eafcff; }
.navbar {
    background: linear-gradient(90deg, #007BFF, #00C2FF);
    padding: 10px;
    display: flex;
    justify-content: center;
    gap: 18px;
    border-radius: 0 0 12px 12px;
}
.navbar button {
    background: none;
    border: none;
    color: white;
    font-weight: 600;
    cursor: pointer;
    font-size: 16px;
}
.navbar button:hover { text-decoration: underline; }
.stButton>button {
    background: linear-gradient(90deg,#00C2FF,#007BFF);
    color: white;
    border-radius: 10px;
    font-weight: 600;
}
.stButton>button:hover { background: linear-gradient(90deg,#007BFF,#00C2FF); }
</style>
""", unsafe_allow_html=True)

# -------------------- NAVBAR --------------------
pages = ["Home", "AnyVideo", "Audio", "TikTok", "Instagram", "Cookie", "About"]
icons = ["🏠", "🎞️", "🎧", "🎬", "📸", "⚙️", "💡"]
cols = st.columns(len(pages))
for i, p in enumerate(pages):
    with cols[i]:
        if st.button(f"{icons[i]} {p}"):
            st.session_state["page"] = p
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
page = st.session_state["page"]

# -------------------- UTILITIES --------------------
def fetch_video_links(profile_url, limit=20):
    """Fetch all videos from TikTok/Instagram account using yt-dlp."""
    ydl_opts = {"quiet": True, "extract_flat": True, "force_generic_extractor": False}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(profile_url, download=False)
        entries = info.get("entries", [])
        return [entry.get("url") for entry in entries if entry.get("url")][:limit]

def download_and_zip_videos(video_urls, limit):
    """Download selected number of videos and zip them."""
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "videos.zip")

    ydl_opts = {
        "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "format": "mp4"
    }

    downloaded_files = []
    total = min(limit, len(video_urls))
    progress = st.progress(0)
    for i, url in enumerate(video_urls[:total]):
        with YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
                for file in os.listdir(temp_dir):
                    if file.endswith(".mp4") and file not in downloaded_files:
                        downloaded_files.append(os.path.join(temp_dir, file))
            except Exception as e:
                st.warning(f"Skipping one video: {e}")
        progress.progress((i + 1) / total)

    # ZIP
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for f in downloaded_files:
            zipf.write(f, os.path.basename(f))

    return zip_path

def get_download_link(file_path, label="Download ZIP"):
    with open(file_path, "rb") as f:
        data = f.read()
    st.download_button(label=label, data=data, file_name="videos.zip", mime="application/zip")

def generate_download_link(url, format="video"):
    ydl_opts = {"quiet": True, "skip_download": True, "noplaylist": True}
    if format == "audio":
        ydl_opts["format"] = "bestaudio"
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("url"), info.get("title", "file")

def download_page(title, site_hint, format="video"):
    st.header(title)
    url = st.text_input(f"Paste {site_hint} URL below 👇")
    if st.button("🔗 Generate Download Link"):
        if not url:
            st.warning("Please enter a valid URL!")
            return
        with st.spinner("Connecting..."):
            time.sleep(1.2)
        try:
            dl_url, title = generate_download_link(url, format=format)
            if dl_url:
                st.success(f"✅ Ready for: {title}")
                st.markdown(f"[⬇️ Click to Download **{title}**]({dl_url})", unsafe_allow_html=True)
            else:
                st.error("❌ Failed to fetch link.")
        except Exception as e:
            st.error(f"Error: {e}")

# -------------------- PAGE LOGIC --------------------
if page == "Home":
    home_path = Path("home.html")
    if home_path.exists():
        components.html(home_path.read_text(encoding="utf-8"), height=700)
    else:
        st.title("🎬 TechHelp Downloader")
        st.info("Upload your home.html in this folder to show landing page.")

elif page == "AnyVideo":
    download_page("🎞️ Universal Video Downloader", "any video site", "video")

elif page == "Audio":
    download_page("🎧 Audio Extractor (MP3)", "YouTube or any site", "audio")

elif page == "TikTok":
    st.header("🎬 TikTok Account Downloader")
    profile = st.text_input("Paste TikTok profile URL 👇")
    if st.button("📂 Fetch All Videos"):
        with st.spinner("Fetching video list..."):
            try:
                videos = fetch_video_links(profile, limit=50)
                if not videos:
                    st.error("No videos found.")
                else:
                    st.success(f"✅ Found {len(videos)} videos.")
                    num = st.number_input("How many videos do you want to download?", 1, min(20, len(videos)), 5)
                    if st.button("⬇️ Download Selected Videos"):
                        with st.spinner("Downloading and zipping..."):
                            zip_path = download_and_zip_videos(videos, int(num))
                            st.success("✅ Done!")
                            get_download_link(zip_path, "📦 Download ZIP")
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "Instagram":
    st.header("📸 Instagram Account Downloader")
    profile = st.text_input("Paste Instagram profile URL 👇")
    if st.button("📂 Fetch All Videos"):
        with st.spinner("Fetching video list..."):
            try:
                videos = fetch_video_links(profile, limit=50)
                if not videos:
                    st.error("No videos found.")
                else:
                    st.success(f"✅ Found {len(videos)} videos.")
                    num = st.number_input("How many videos do you want to download?", 1, min(20, len(videos)), 5)
                    if st.button("⬇️ Download Selected Videos"):
                        with st.spinner("Downloading and zipping..."):
                            zip_path = download_and_zip_videos(videos, int(num))
                            st.success("✅ Done!")
                            get_download_link(zip_path, "📦 Download ZIP")
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "Cookie":
    st.header("⚙️ Cookie Settings (Advanced)")
    st.info("Paste your TikTok/Instagram cookies if login is required.")
    cookie_input = st.text_area("Paste cookie string below 👇")
    if st.button("💾 Save Cookie"):
        st.session_state["cookie"] = cookie_input
        st.success("✅ Cookie saved for this session.")

elif page == "About":
    st.header("💡 About TechHelp Downloader")
    st.markdown("""
    **TechHelp Downloader** — a universal tool for:
    - TikTok, Instagram, YouTube, Audio
    - Bulk download from profiles
    - Chrome-based streaming downloads  
    💻 Built with **Python + Streamlit + yt-dlp**
    """)
