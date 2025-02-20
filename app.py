import streamlit as st
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Thông tin API
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Hàm tạo client_secrets từ Streamlit Secrets
def get_client_secrets():
    return {
        "installed": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [st.secrets["google_oauth"]["redirect_uris"]]
        }
    }

# Hàm xác thực sử dụng token.json và Secrets
def get_authenticated_service():
    if os.path.exists("token.json"):
        try:
            with open("token.json", "r") as token_file:
                token_data = json.load(token_file)
            client_secrets = get_client_secrets()
            credentials = Credentials(
                token=token_data["token"],
                refresh_token=token_data["refresh_token"],
                token_uri=token_data["token_uri"],
                client_id=client_secrets["installed"]["client_id"],
                client_secret=client_secrets["installed"]["client_secret"],
                scopes=SCOPES
            )
            # Làm mới token nếu hết hạn
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            return build("youtube", "v3", credentials=credentials)
        except Exception as e:
            st.error(f"Lỗi xác thực: {str(e)}")
            return None
    st.error("Không tìm thấy token.json trong repository!")
    return None

# Hàm lấy danh sách kênh từ YouTube API
def get_channel_list(youtube):
    try:
        request = youtube.channels().list(
            part="snippet",
            mine=True
        )
        response = request.execute()
        channels = {item["snippet"]["title"]: item["id"] for item in response["items"]}
        return channels
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách kênh: {str(e)}")
        return {}

# Hàm upload video
def upload_video(youtube, video_path, title, description, tags, category_id="22"):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags.split(","),
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    media = MediaFileUpload(video_path)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response["id"]

# Hàm kiểm tra mật khẩu
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        password = st.text_input("Nhập mật khẩu", type="password")
        if st.button("Xác nhận"):
            if password == "YOUR_PASSWORD":  # Thay bằng mật khẩu của bạn
                st.session_state.authenticated = True
                st.success("Đăng nhập thành công!")
            else:
                st.error("Mật khẩu sai!")
        return False
    return True

# Giao diện Streamlit
st.title("YouTube Video Uploader (Private)")

# Kiểm tra mật khẩu trước khi hiển thị giao diện
if check_password():
    # Khởi tạo YouTube API
    youtube = get_authenticated_service()

    if youtube:
        # Lấy danh sách kênh
        channels = get_channel_list(youtube)
        if channels:
            selected_channel = st.selectbox("Chọn kênh để upload", list(channels.keys()))

            video_file = st.file_uploader("Chọn video", type=["mp4"])
            title = st.text_input("Tiêu đề video")
            description = st.text_area("Mô tả video")
            tags = st.text_input("Tags (phân cách bằng dấu phẩy)", "tag1, tag2, tag3")
            category_id = st.selectbox("Danh mục", ["22"], help="22 là People & Blogs")

            if st.button("Upload"):
                if video_file and title and description and tags:
                    with open("temp_video.mp4", "wb") as f:
                        f.write(video_file.read())
                    try:
                        video_id = upload_video(youtube, "temp_video.mp4", title, description, tags)
                        st.success(f"Video uploaded vào kênh '{selected_channel}'! ID: {video_id}")
                    except Exception as e:
                        st.error(f"Lỗi khi upload: {str(e)}")
                else:
                    st.error("Vui lòng điền đầy đủ thông tin!")
        else:
            st.error("Không thể lấy danh sách kênh!")
    else:
        st.error("Không thể xác thực API. Kiểm tra token.json!")