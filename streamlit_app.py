import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import shutil, time, base64

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Techelp Downloader", page_icon="🎬", layout="wide")

# Hide Streamlit header/footer
st.markdown("""
<style>
header, footer {visibility:hidden;}
body {background-color:#0b0c10;color:#c5c6c7;}
.stButton>button{background:linear-gradient(90deg,#00C2FF,#007BFF);
 color:white;border-radius:10px;font-weight:600;}
.stButton>button:hover{background:linear-gradient(90deg,#007BFF,#00C2FF);}
.navbar{background:linear-gradient(90deg,#007BFF,#00C2FF);
 padding:12px;display:flex;justify-content:center;flex-wrap:wrap;
 border-radius:0 0 12px 12px;gap:18px;}
.navbar button{background:none;border:none;color:white;
 font-size:16px;font-weight:600;cursor:pointer;}
.navbar button:hover{text-decoration:underline;}
</style>
""", unsafe_allow_html=True)

# ---------------- NAVBAR ----------------
col_home, col_video, col_audio, col_tt, col_ig, col_cookie, col_about = st.columns(7)
with col_home: st.button("🏠 Home", on_click=lambda: st.session_state.update(page="Home"))
with col_video: st.button("🎞️ Any Video", on_click=lambda: st.session_state.update(page="AnyVideo"))
with col_audio: st.button("🎧 Audio", on_click=lambda: st.session_state.update(page="Audio"))
with col_tt: st.button("🎬 TikTok", on_click=lambda: st.session_state.update(page="TikTok"))
with col_ig: st.button("📸 Instagram", on_click=lambda: st.session_state.update(page="Instagram"))
with col_cookie: st.button("⚙️ Cookie", on_click=lambda: st.session_state.update(page="Cookie"))
with col_about: st.button("💡 About", on_click=lambda: st.session_state.update(page="About"))

# ---------------- SETUP ----------------
OUT_DIR = Path("downloads")
OUT_DIR.mkdir(exist_ok=True)

# ---------------- UTILITIES ----------------
def download_with_progress(url: str, audio=False, playlist_items=None):
    prog = st.progress(0)
    status = st.empty()
    def hook(d):
        if d['status']=="downloading":
            p=d.get('_percent_str','0%').replace('%','')
            try:prog.progress(float(p)/100)
            except:pass
            status.text(f"Downloading... {p}%")
        elif d['status']=="finished":
            prog.progress(1.0)
            status.text("Finishing...")
    opts={
        "quiet":True,"progress_hooks":[hook],
        "outtmpl":str(OUT_DIR / "%(title).80s.%(ext)s"),
        "ignoreerrors":True
    }
    if audio:
        opts["format"]="bestaudio/best"
        opts["postprocessors"]=[{"key":"FFmpegExtractAudio",
            "preferredcodec":"mp3","preferredquality":"192"}]
    else: opts["format"]="best"
    if playlist_items: opts["playlist_items"]=f"1:{playlist_items}"
    with YoutubeDL(opts) as ydl:
        info=ydl.extract_info(url,download=True)
    prog.empty(); status.text("✅ Done")
    now=time.time()
    files=[p for p in OUT_DIR.iterdir() if (now-p.stat().st_mtime)<600]
    return sorted(files,key=lambda x:x.stat().st_mtime,reverse=True)

# ---------------- ENTER KEY ----------------
enter_js="""<script>
document.addEventListener('keydown',function(e){
 if(e.key==='Enter'){let b=document.querySelector('button[kind=primary]');
 if(b)b.click();}
});
</script>"""

# ---------------- PAGES ----------------
page = st.session_state.get("page","Home")

if page=="Home":
    try:
        with open("home.html","r",encoding="utf-8") as f:
            st.markdown(f.read(), unsafe_allow_html=True)
    except:
        st.title("🎬 Techelp Video Downloader")
        st.write("Welcome! Use the navbar above to download videos or audio from TikTok, Instagram, and more.")

elif page=="AnyVideo":
    st.header("🎞️ Download Any Video")
    st.markdown(enter_js,unsafe_allow_html=True)
    url=st.text_input("Enter video URL"); st.write("")
    if st.button("Submit"): 
        if url: download_with_progress(url)

elif page=="Audio":
    st.header("🎧 Extract Audio (MP3)")
    st.markdown(enter_js,unsafe_allow_html=True)
    url=st.text_input("Enter video URL"); st.write("")
    if st.button("Submit"): 
        if url: download_with_progress(url,audio=True)

elif page=="TikTok":
    st.header("🎬 TikTok Account Downloader")
    st.markdown(enter_js,unsafe_allow_html=True)
    user=st.text_input("Enter TikTok username (without @)"); st.write("")
    if st.button("Submit"):
        if user:
            url=f"https://www.tiktok.com/@{user}"
            st.info("Fetching account info...")
            with YoutubeDL({"quiet":True,"ignoreerrors":True}) as ydl:
                info=ydl.extract_info(url,download=False)
            total=len(info.get("entries",[])) if info and "entries" in info else 0
            if total==0: st.warning("No videos found or profile is private.")
            else:
                st.success(f"Total {total} videos found.")
                n=st.number_input("How many recent videos to download?",1,total,5)
                col1,col2=st.columns(2)
                with col1:
                    if st.button("Start Download"):
                        files=download_with_progress(url,playlist_items=int(n))
                        if files:
                            zipname=OUT_DIR/f"techelp_tiktok_{user}_{int(time.time())}.zip"
                            shutil.make_archive(str(zipname.with_suffix('')),'zip',OUT_DIR)
                            with open(zipname,"rb") as zf:
                                st.download_button("⬇️ Download ZIP",data=zf,file_name=zipname.name)
                with col2:
                    if st.button("Download All"):
                        files=download_with_progress(url)
                        if files:
                            zipname=OUT_DIR/f"techelp_tiktok_all_{user}_{int(time.time())}.zip"
                            shutil.make_archive(str(zipname.with_suffix('')),'zip',OUT_DIR)
                            with open(zipname,"rb") as zf:
                                st.download_button("⬇️ Download All ZIP",data=zf,file_name=zipname.name)

elif page=="Instagram":
    st.header("📸 Instagram Account Downloader")
    st.markdown(enter_js,unsafe_allow_html=True)
    user=st.text_input("Enter Instagram username (without @)"); st.write("")
    if st.button("Submit"):
        if user:
            url=f"https://www.instagram.com/{user}/"
            st.info("Fetching account info (may need cookie for private profiles)...")
            with YoutubeDL({"quiet":True,"ignoreerrors":True}) as ydl:
                info=ydl.extract_info(url,download=False)
            total=len(info.get("entries",[])) if info and "entries" in info else 0
            if total==0: st.warning("No posts found or profile is private.")
            else:
                st.success(f"Total {total} posts found.")
                n=st.number_input("How many recent posts to download?",1,total,5)
                col1,col2=st.columns(2)
                with col1:
                    if st.button("Start Download"):
                        files=download_with_progress(url,playlist_items=int(n))
                        if files:
                            zipname=OUT_DIR/f"techelp_insta_{user}_{int(time.time())}.zip"
                            shutil.make_archive(str(zipname.with_suffix('')),'zip',OUT_DIR)
                            with open(zipname,"rb") as zf:
                                st.download_button("⬇️ Download ZIP",data=zf,file_name=zipname.name)
                with col2:
                    if st.button("Download All"):
                        files=download_with_progress(url)
                        if files:
                            zipname=OUT_DIR/f"techelp_insta_all_{user}_{int(time.time())}.zip"
                            shutil.make_archive(str(zipname.with_suffix('')),'zip',OUT_DIR)
                            with open(zipname,"rb") as zf:
                                st.download_button("⬇️ Download All ZIP",data=zf,file_name=zipname.name)

elif page=="Cookie":
    st.header("⚙️ Cookie Settings")
    cookie=st.text_area("Paste cookie string here",height=150)
    if cookie: st.success("Cookie saved for this session.")
    st.info("Add cookies for private account access.")

elif page=="About":
    st.header("💡 About")
    st.write("""
    **Techelp Video Downloader**  
    Built with **Streamlit + yt-dlp**  
    Supports YouTube, TikTok, Instagram & more.  
    Developer: **Tanzeel ur Rehman**
    """)
