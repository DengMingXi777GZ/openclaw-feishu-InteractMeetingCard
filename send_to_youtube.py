#!/usr/bin/env python3
"""
真正自动YouTube上传工具 - 使用Refresh Token
实现完全自动化的视频上传
"""

import json
import os
import sys
import pickle
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

def get_authenticated_service():
    """获取认证服务 - 使用Refresh Token"""
    
    token_path = os.path.expanduser('~/.youtube_credentials/token.pickle')
    
    if not os.path.exists(token_path):
        return None, f"Token文件不存在: {token_path}"
    
    try:
        with open(token_path, 'rb') as f:
            creds = pickle.load(f)
        
        # 检查令牌是否过期，如果过期则刷新
        if creds.expired and creds.refresh_token:
            print("🔄 Refresh Token 过期，正在刷新...")
            creds.refresh(Request())
            # 保存刷新后的令牌
            with open(token_path, 'wb') as f:
                pickle.dump(creds, f)
            print("✅ Refresh Token 刷新成功！")
        
        print(f"✅ Token 有效期: {creds.expiry}")
        print(f"✅ Refresh Token: {'有' if creds.refresh_token else '无'}")
        print(f"✅ 已授权范围: {creds.scopes}")
        
        return build('youtube', 'v3', credentials=creds), None
        
    except Exception as e:
        return None, f"加载token失败: {e}"

def upload_video(video_path, title, description="", privacy="private", tags=None):
    """上传视频到YouTube"""
    
    if not os.path.exists(video_path):
        return {"success": False, "error": f"文件不存在: {video_path}"}
    
    print(f"🚀 开始上传: {os.path.basename(video_path)}")
    print(f"📊 文件大小: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
    
    try:
        # 获取认证服务
        youtube, error = get_authenticated_service()
        if error:
            return {"success": False, "error": error}
        
        print("📝 准备上传元数据...")
        
        # 准备视频元数据
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags or [],
                'categoryId': '28'  # Science & Technology
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False
            }
        }
        
        print("📁 准备视频文件...")
        
        # 创建媒体文件上传对象
        media = MediaFileUpload(
            video_path, 
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        print("⬆️ 开始上传...")
        
        # 创建上传请求
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        # 执行上传
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"⏫ 上传进度: {int(status.progress() * 100)}%")
        
        print("✅ 上传完成！")
        
        return {
            "success": True,
            "video_id": response['id'],
            "video_url": f"https://youtu.be/{response['id']}",
            "title": title
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_tool(tool_name, parameters):
    """执行工具"""
    if tool_name == "upload_video":
        return upload_video(**parameters)
    return {"success": False, "error": f"未知工具: {tool_name}"}

if __name__ == "__main__":
    if not sys.stdin.isatty():
        params = json.load(sys.stdin)
    else:
        params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    
    result = execute_tool("upload_video", params)
    print(json.dumps(result, ensure_ascii=False, indent=2))