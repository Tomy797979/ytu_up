import streamlit as st
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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

# Hàm xác thực sử dụng token.json
def get_authenticated_service():
    if os.path.exists("token.json"):
        with open("token.json", "r") as token_file:
            token_data = json.load(token_file)
        credentials = Credentials(
            token=token_data["token"],
            refresh_token=token_data["refresh_token"],
            token_uri=token_data["token_uri"],
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scopes=token_data["scopes"]
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh()
        return build("youtube", "v3", credentials=credentials)
    st.error("Không tìm thấy token.json trong repository!")
    return None

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
            "privacyStatus": "public"  # Có thể đổi thành "private" hoặc "unlisted"
        }
    }
    media = MediaFileUpload(video_path)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response["id"]

# Giao diện Streamlit
st.title("YouTube Video Uploader")
video_file = st.file_uploader("Chọn video", type=["mp4"])
title = st.text_input("Tiêu đề video")
description = st.text_area("Mô tả video")
tags = st.text_input("Tags (phân cách bằng dấu phẩy)", "tag1, tag2, tag3")
category_id = st.selectbox("Danh mục", ["22"], help="22 là People & Blogs")

if st.button("Upload"):
    if video_file and title and description and tags:
        # Lưu file video tạm thời
        with open("temp_video.mp4", "wb") as f:
            f.write(video_file.read())
        
        youtube = get_authenticated_service()
        if youtube:
            try:
                video_id = upload_video(youtube, "temp_video.mp4", title, description, tags)
                st.success(f"Video uploaded! ID: {video_id}")
            except Exception as e:
                st.error(f"Lỗi khi upload: {str(e)}")
        else:
            st.error("Không thể xác thực API. Kiểm tra token.json!")
    else:
        st.error("Vui lòng điền đầy đủ thông tin!")
