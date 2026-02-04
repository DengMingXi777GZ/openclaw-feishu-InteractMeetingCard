# OpenClaw Skill开发指南：语音输入，生成飞书互动式会议卡片（联动Seeed Studio reSpeaker XVF 3800）

> ---
> 想让你的机器人具备语音交互能力？试试 Seeed Studio 的 ReSpeaker 系列吧！
> **reSpeaker XVF3800** 是一款基于 XMOS XVF3800 芯片的专业级 4 麦克风圆形阵列麦克风，即使在嘈杂的环境中也能清晰地拾取目标语音。它具备双模式、360° 远场语音拾取（最远 5 米）、自动回声消除 (AEC)、自动增益控制 (AGC)、声源定位 (DoA)、去混响、波束成形和噪声抑制等功能。结合飞书 OpenClaw 机器人，您可以打造语音唤醒 + AI 智能回复的完整办公助手解决方案。
> [项目源码仓库](https://github.com/DengMingXi777GZ/openclaw-feishu-InteractMeetingCard)
> [ReSpeaker产品源码](https://github.com/respeaker)
> [ReSpeaker 四麦克风阵列 | Seeed Studio 购买链接](https://www.seeedstudio.com.cn/product/respeaker-mic-array-v2-0)
> 
> ![reSpeaker XVF3800](https://files.seeedstudio.com/wiki/respeaker_xvf3800_usb/respeaker-banner.jpg)
> ---

## 结果展示

以下是本项目的实际运行效果演示：

### 演示视频

![Demo GIF](demo.gif)

### 功能演示说明

视频中展示了完整的语音交互流程：

1. **语音唤醒** - 使用ReSpeaker麦克风阵列进行语音采集
2. **语音识别** - Whisper模型实时识别语音指令
3. **信息提取** - 自动解析会议主题、时间、地点、参与者
4. **卡片生成** - 创建精美的飞书互动式会议卡片
5. **一键发送** - 卡片发送到指定飞书群组
6. **日程创建** - 点击卡片按钮直接在飞书日历创建事件

### 实际效果截图

运行成功后，飞书群组将收到如下互动式卡片：

![alt text](image.png)

---

## 项目背景

在开发语音助手项目时，我发现需要创建一个能够发送飞书互动式会议卡片的Skill。与普通的文本消息不同，互动式卡片需要特殊的JSON结构和飞书API支持，这促使我深入研究OpenClaw的Skill开发机制。

本项目结合语音识别、自然语言处理和飞书API，实现了通过**语音输入**自动创建并发送互动式会议邀请卡片到飞书群组的功能。

## 语音输入功能

本项目支持通过语音指令创建会议卡片，以下是完整的语音输入解决方案：

### 语音输入处理流程

```python
# 示例语音输入
"Schedule a meeting with Tom tomorrow at 3pm in Room 1"

# 系统解析结果:
{
    "topic": "Meeting",
    "date": "2024-01-15",
    "time": "15:00",
    "attendees": ["Tom"],
    "location": "Room 1",
    "duration": 60
}
```

### 语音识别配置

#### 1. 硬件要求
- **ReSpeaker 4-Mic Array** - 4麦克风圆形阵列
- 2GB+ RAM
- 网络连接

#### 2. 安装语音识别模型

```bash
# 下载Whisper模型
mkdir -p ~/moltbot/asr_model_en
cd ~/moltbot/asr_model_en

# 下载tiny.en模型文件
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/tiny.en-encoder.onnx
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/tiny.en-decoder.onnx
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/tiny.en-tokens.txt
```

#### 3. 语音指令示例

**英文指令：**
- `"Schedule a meeting with Tom tomorrow at 3pm"`
- `"Book a review meeting today at 2pm in Room 1"`
- `"Create a discussion next Monday at 10am"`

**中文指令：**
- `"明天下午3点和Tom开会"`
- `"今天2点在会议室1开评审会"`
- `"下周一上午10点创建讨论会"`

### 语音输入运行流程

1. **语音识别** - 5秒录音，Whisper模型识别
2. **信息解析** - 提取时间、人员、地点等信息
3. **卡片生成** - 创建飞书互动式会议卡片
4. **群组发送** - 发送到配置的飞书群组
5. **结果反馈** - 显示发送状态和卡片ID

### 启动语音输入程序

```bash
cd ~/feishu_card
python3 Demo.py
```

---

## Skill开发完整流程

### 第一步：理解OpenClaw Skill架构

OpenClaw的Skill系统基于模块化设计，每个Skill都是一个独立的Python模块，通过特定的接口与OpenClaw核心系统交互。

**关键概念：**
- **Skill目录**: `~/.openclaw/skills/[skill_name]/`
- **入口文件**: `__init__.py` 或指定的Python文件
- **工具注册**: 通过`@tool`装饰器注册函数
- **配置文件**: `SKILL.md` 提供使用说明

### 第二步：创建Skill基础结构

#### 1. 创建Skill目录
```bash
mkdir -p ~/.openclaw/skills/feishu_meeting
cd ~/.openclaw/skills/feishu_meeting
```

#### 2. 创建核心文件
```bash
touch __init__.py
touch send_meeting_card.py
touch SKILL.md
```

### 第三步：编写核心功能代码

#### 1. 主功能文件：`send_meeting_card.py`

```python
#!/usr/bin/env python3
"""
飞书会议卡片发送模块
用于OpenClac Skill系统，创建并发送交互式会议邀请卡片
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

def create_meeting_card(params: Dict[str, Any]) -> Dict[str, Any]:
    """创建飞书交互式会议卡片"""
    
    # 参数提取和默认值处理
    topic = params.get("topic", "会议")
    date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
    time = params.get("time", "15:00")
    attendees = params.get("attendees", [])
    location = params.get("location", "待定")
    duration = params.get("duration", 60)
    
    # 构建参与人字符串
    attendees_str = ", ".join(attendees) if attendees else "待定"
    
    # 创建飞书互动式卡片结构
    card_content = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📅 {topic}"
                },
                "template": "blue"  # 蓝色主题
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**🕐 时间：** {date} {time}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**👥 参与人：** {attendees_str}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📍 地点：** {location}"
                    }
                },
                {
                    "tag": "hr"  # 分隔线
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "创建日程"
                            },
                            "type": "primary",
                            "value": {
                                "action": "create_calendar_event",
                                "meeting_data": {
                                    "topic": topic,
                                    "date": date,
                                    "time": time,
                                    "duration": duration,
                                    "attendees": attendees,
                                    "location": location
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    return card_content

def send_meeting_card(params: Dict[str, Any]) -> Dict[str, Any]:
    """发送会议卡片到飞书群组"""
    
    try:
        # 创建卡片内容
        card_content = create_meeting_card(params)
        
        # 获取群组ID（可以在参数中指定，也可以使用默认值）
        group_chat_id = params.get("group_chat_id", "your-group-chat-id")  # 请替换为您的飞书群组ID
        
        # 使用OpenClaw的message工具发送
        # 这里需要调用OpenClaw的message功能
        result = send_feishu_message(group_chat_id, card_content)
        
        if result.get("success"):
            return {
                "success": True,
                "message_id": result.get("message_id"),
                "group": params.get("group_name", "群组")
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "发送失败")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"发送异常: {str(e)}"
        }

def send_feishu_message(target: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """通过OpenClaw发送飞书消息"""
    try:
        # 导入OpenClaw的message工具
        from tools import message
        
        # 发送消息
        response = message.send(
            channel="feishu",
            target=target,
            message=json.dumps(content, ensure_ascii=False)
        )
        
        return {"success": True, "message_id": response.get("message_id")}
        
    except ImportError:
        # 如果直接运行，使用备用方案
        import subprocess
        import json
        
        try:
            cmd = [
                "openclaw", "message", "send",
                "--channel", "feishu",
                "--target", target,
                "--message", json.dumps(content, ensure_ascii=False)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {"success": True, "message_id": "sent_via_cli"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """主函数 - 支持命令行调用"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("用法: python3 send_meeting_card.py '{\"topic\": \"会议\", \"time\": \"15:00\"}'")
            return
            
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print("错误: 无效的JSON格式")
            return
    else:
        # 默认测试数据
        params = {
            "topic": "项目评审会议",
            "date": "2024-01-15",
            "time": "15:00",
            "attendees": ["张三", "李四"],
            "location": "会议室A"
        }
    
    result = send_meeting_card(params)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
```

#### 2. 初始化文件：`__init__.py`

```python
"""
Feishu Meeting Skill - 飞书会议卡片Skill
"""

from .send_meeting_card import send_meeting_card, create_meeting_card

# 导出主要功能
__all__ = ['send_meeting_card', 'create_meeting_card']
```

#### 3. 文档文件：`SKILL.md`

```markdown
# Feishu Meeting Skill

**MANDATORY TOOL FOR MEETING SCHEDULING**
When user wants to schedule/create/arrange a meeting, you MUST use this tool.
This tool creates professional interactive meeting cards with calendar buttons.
Do NOT use the generic &quot;message&quot; tool - it cannot create interactive cards.

## 功能说明

这个Skill专门用于创建和发送飞书互动式会议邀请卡片，支持：
- 📅 交互式会议卡片
- 🔗 一键创建日程按钮
- 👥 参与人管理
- 📍 地点设置
- ⏰ 时间提醒

## 使用方法

### 基本用法
```python
from tools import feishu_meeting

# 创建会议
feishu_meeting.create(
    topic="项目评审会议",
    date="2024-01-15",
    time="15:00",
    attendees=["张三", "李四"],
    location="会议室A",
    duration=60,
    group_name="项目团队"
)
```

### 参数说明
- `topic`: 会议主题
- `date`: 会议日期 (YYYY-MM-DD)
- `time`: 会议时间 (HH:MM)
- `attendees`: 参与人列表
- `location`: 会议地点
- `duration`: 会议时长(分钟)
- `group_name`: 群组名称

### 命令行使用
```bash
python3 send_meeting_card.py '{"topic": "周会", "time": "14:00"}'
```
```

### 第四步：集成到OpenClaw系统

#### 最重要的解决方法：让openclaw自己debug
我们使用的是一个ai，我在实验中有遇到我写好了skills，但是openclaw没有识别出来的情况，后来我让openclaw自己debug，他进行了一些黑箱操作，自动识别完成了，这个办法在我后续的项目中依然生效。

```bash
# 打开opoenclaw对话框进行自我debug，告诉openclaw，你已经写好的skills的位置，让他自己进行注册和配置。
openclaw dashboard
```


#### 1. 工具注册

为了让OpenClaw识别这个Skill，需要在适当的配置文件中注册。通常OpenClaw会自动扫描`~/.openclaw/skills/`目录下的Skill。

#### 2. 配置认证信息

确保在OpenClaw中配置了飞书应用的认证信息：

```json
// ~/.openclaw/agents/main/agent/auth-profiles.json
{
  "feishu": {
    "appId": "cli_xxxxxxxx",
    "appSecret": "xxxxxxxxxx",
    "verificationToken": "xxxxxxxxxx",
    "encryptKey": "xxxxxxxxxx"
  }
}
```

#### 3. 测试Skill功能

```bash
# 进入Skill目录
cd ~/.openclaw/skills/feishu_meeting

# 测试基本功能
python3 send_meeting_card.py

# 带参数测试
python3 send_meeting_card.py '{"topic": "测试会议", "time": "16:00", "attendees": ["测试用户"]}'
```

### 第五步：在OpenClaw中使用Skill

#### 1. 通过Agent调用

当用户说："安排一个会议"时，OpenClaw应该自动调用这个Skill：

```python
# 在Agent的处理逻辑中
from tools import feishu_meeting

# 解析用户意图并调用Skill
feishu_meeting.create(
    topic=extracted_topic,
    date=extracted_date,
    time=extracted_time,
    attendees=extracted_attendees,
    location=extracted_location
)
```

#### 2. 直接命令行调用

```bash
openclaw message send --channel feishu --target [group_id] --message '[卡片内容]'
```

## 关键技术要点

### 1. 飞书卡片格式

飞书互动式卡片需要特定的JSON结构：
- `msg_type`: 必须是"interactive"
- `card`: 包含完整的卡片定义
- `elements`: 定义卡片的各个组件
- `actions`: 定义交互按钮

### 2. 错误处理机制

```python
try:
    # 主要逻辑
    result = send_feishu_message(target, card_content)
    if result.get("success"):
        return {"success": True, "message_id": result["message_id"]}
    else:
        return {"success": False, "error": result.get("error")}
except Exception as e:
    return {"success": False, "error": f"异常: {str(e)}"}
```

### 3. 兼容性考虑

- **OpenClaw集成模式**: 通过`from tools import message`
- **独立运行模式**: 通过subprocess调用openclaw命令
- **命令行模式**: 直接处理JSON参数

## 调试和故障排除

### 1. 常见问题

**问题1**: Skill未被识别
- 检查目录结构是否正确
- 确认`__init__.py`文件存在
- 查看OpenClaw日志

**问题2**: 认证失败
- 检查飞书应用配置
- 确认认证信息正确
- 验证应用权限

**问题3**: 卡片发送失败
- 检查群组ID是否正确
- 验证卡片JSON格式
- 查看网络连接

### 2. 调试技巧

```bash
# 启用调试模式
export OPENCLAW_DEBUG=1

# 查看日志
tail -f ~/.openclaw/logs/gateway.log

# 手动测试卡片JSON
python3 -c "import json; print(json.dumps(card_content, indent=2))"
```

### 3. 验证步骤

1. **Skill识别验证**
   ```bash
   openclaw skills list
   ```

2. **认证验证**
   ```bash
   # 测试飞书API连接
   python3 -c "from tools import message; print('OK')"
   ```

3. **功能验证**
   ```bash
   # 测试卡片创建
   python3 send_meeting_card.py
   ```
