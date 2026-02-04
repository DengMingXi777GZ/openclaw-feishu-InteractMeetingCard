# OpenClaw 自动上传 YouTube 视频指南

> 让 OpenClaw 机器人自动将生成的视频上传到 YouTube 频道

---

## 功能概述

本工具实现了 OpenClaw 与 YouTube Data API 的无缝集成，允许通过语音指令或自动化流程将视频文件上传到指定的 YouTube 频道。

### 核心特性

- ✅ **全自动上传** - 无需人工干预，支持后台自动上传
- ✅ **断点续传** - 支持大视频文件的分块上传，中断后可恢复
- ✅ **Refresh Token 认证** - 一次授权，长期有效
- ✅ **元数据配置** - 支持自定义标题、描述、标签和隐私设置
- ✅ **OpenClaw 集成** - 作为 Skill 工具被 OpenClaw 调用

---

## 前置要求

### 1. 创建 Google Cloud 项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **YouTube Data API v3**：
   - 进入 "APIs & Services" → "Library"
   - 搜索 "YouTube Data API v3" 并启用

### 2. 配置 OAuth 2.0 凭据

1. 进入 "APIs & Services" → "Credentials"
2. 点击 "Create Credentials" → "OAuth client ID"
3. 选择应用类型："Desktop app"
4. 记下生成的 **Client ID** 和 **Client Secret**

### 3. 获取 Refresh Token

创建 `get_refresh_token.py` 脚本获取长期有效的 Refresh Token：

```python
#!/usr/bin/env python3
"""获取 YouTube API 的 Refresh Token"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# OAuth 2.0 配置
CLIENT_ID = "your-client-id"          # 替换为您的 Client ID
CLIENT_SECRET = "your-client-secret"  # 替换为您的 Client Secret
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_refresh_token():
    """获取并保存 Refresh Token"""
    
    # 创建客户端配置
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
        }
    }
    
    # 创建认证流程
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    
    # 运行本地服务器获取授权
    creds = flow.run_local_server(port=0)
    
    # 保存凭据
    creds_dir = os.path.expanduser('~/.youtube_credentials')
    os.makedirs(creds_dir, exist_ok=True)
    
    token_path = os.path.join(creds_dir, 'token.pickle')
    with open(token_path, 'wb') as f:
        pickle.dump(creds, f)
    
    print(f"✅ 凭据已保存到: {token_path}")
    print(f"📋 Refresh Token: {creds.refresh_token}")
    print(f"⏰ 过期时间: {creds.expiry}")
    
    return creds

if __name__ == "__main__":
    get_refresh_token()
```

**运行步骤：**

```bash
# 安装依赖
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# 运行获取 Token
python get_refresh_token.py
```

运行后会弹出浏览器窗口，登录您的 YouTube 账号并授权。成功后，token 将保存在 `~/.youtube_credentials/token.pickle`。

---

## OpenClaw Skill 配置

### 1. 文件结构

将 `send_to_youtube.py` 放入 OpenClaw Skill 目录：

```
~/.openclaw/skills/youtube_uploader/
├── __init__.py
├── send_to_youtube.py
└── SKILL.md
```

### 2. Skill 注册文件

创建 `__init__.py`：

```python
"""YouTube 视频上传 Skill"""
from .send_to_youtube import upload_video, execute_tool

__all__ = ['upload_video', 'execute_tool']
```

### 3. Skill 文档

创建 `SKILL.md`：

```markdown
# YouTube Video Uploader

**MANDATORY TOOL FOR VIDEO UPLOADING**
When user wants to upload a video to YouTube, you MUST use this tool.

## 功能说明

自动上传视频文件到 YouTube 频道，支持自定义标题、描述和隐私设置。

## 使用方法

### 基本用法
```python
from tools import youtube_uploader

result = youtube_uploader.upload_video(
    video_path="/path/to/video.mp4",
    title="视频标题",
    description="视频描述",
    privacy="private",  # private/unlisted/public
    tags=["标签1", "标签2"]
)
```

### 参数说明
- `video_path`: 视频文件的完整路径
- `title`: 视频标题（必填）
- `description`: 视频描述（可选）
- `privacy`: 隐私设置 - private(私有)/unlisted(不公开)/public(公开)
- `tags`: 标签列表（可选）

### 返回值
```json
{
    "success": true,
    "video_id": "xxxxxxxxxxx",
    "video_url": "https://youtu.be/xxxxxxxxxxx",
    "title": "视频标题"
}
```
```

---

## 使用示例

### 命令行直接调用

```bash
# 基础上传
python send_to_youtube.py '{
    "video_path": "/home/user/videos/demo.mp4",
    "title": "OpenClaw 飞书会议卡片演示",
    "description": "展示如何使用语音创建飞书会议卡片",
    "privacy": "public",
    "tags": ["OpenClaw", "Feishu", "Voice Assistant"]
}'
```

### OpenClaw 工作流集成

```python
# 在 OpenClaw Agent 中调用
from tools import youtube_uploader

def process_video_request(video_info):
    """处理视频上传请求"""
    
    # 上传视频
    result = youtube_uploader.upload_video(
        video_path=video_info['path'],
        title=video_info['title'],
        description=video_info.get('description', ''),
        privacy=video_info.get('privacy', 'private'),
        tags=video_info.get('tags', [])
    )
    
    if result['success']:
        return f"✅ 视频上传成功！\n🔗 链接: {result['video_url']}"
    else:
        return f"❌ 上传失败: {result['error']}"
```

### 语音指令示例

用户可以说：
- *"把刚才录制的视频上传到 YouTube，标题叫项目演示"*
- *"上传 /home/user/video.mp4 到 YouTube，设为公开"*
- *"将这个会议录像发布到我的 YouTube 频道"*

OpenClaw 将自动解析意图并调用上传工具。

---

## 安全注意事项

### 1. 凭据保护

⚠️ **切勿将以下内容提交到 Git 仓库：**

```bash
# 添加到 .gitignore
~/.youtube_credentials/
*.pickle
get_refresh_token.py  # 包含 client_id 和 client_secret
```

### 2. Token 文件权限

```bash
# 设置适当的文件权限
chmod 600 ~/.youtube_credentials/token.pickle
```

### 3. 定期轮换

- Refresh Token 长期有效，但建议定期重新授权
- 在 Google Cloud Console 中可撤销已颁发的 Token

---

## 故障排除

### 1. Token 过期问题

```bash
# 重新获取 Token
python get_refresh_token.py
```

### 2. API 配额限制

YouTube Data API 有每日配额限制（默认 10,000 units）：
- 每次视频上传约消耗 1600 units
- 可在 Google Cloud Console 申请提高配额

### 3. 上传失败常见原因

| 错误 | 解决方案 |
|------|----------|
| `Token file not found` | 运行 `get_refresh_token.py` 重新授权 |
| `Invalid credentials` | 检查 Client ID 和 Secret 是否正确 |
| `Quota exceeded` | 等待配额重置或申请提高配额 |
| `Video too large` | 确保视频文件小于 128GB |

---

## 进阶配置

### 自定义上传参数

在 `send_to_youtube.py` 中可修改的默认配置：

```python
# 视频分类（Category ID）
'categoryId': '28'  # 28 = Science & Technology

# 其他常用分类：
# 1 = Film & Animation
# 2 = Autos & Vehicles
# 10 = Music
# 15 = Pets & Animals
# 17 = Sports
# 20 = Gaming
# 22 = People & Blogs
# 23 = Comedy
# 24 = Entertainment
# 25 = News & Politics
# 26 = Howto & Style
# 27 = Education
```

### 分块上传配置

调整上传性能和稳定性：

```python
media = MediaFileUpload(
    video_path, 
    resumable=True,
    chunksize=1024*1024  # 1MB 分块，可调整为 256KB-64MB
)
```

---

## 参考资料

- [YouTube Data API 文档](https://developers.google.com/youtube/v3/docs)
- [Google OAuth 2.0 指南](https://developers.google.com/identity/protocols/oauth2)
- [OpenClaw Skill 开发文档](https://github.com/your-repo/openclaw-skills)

---

**项目状态**: 功能完整，可生产使用  
**最后更新**: 2025年1月  
**版本**: v1.0.0
