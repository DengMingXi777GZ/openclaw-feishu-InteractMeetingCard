#!/usr/bin/env python3
"""
Moltbot Voice Meeting Assistant - 最终整合版
ReSpeaker 语音 → ASR → OpenClaw Skill → 飞书交互式卡片
"""

import subprocess
import sys
import os
import json
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from asr_english import RespeakerASR

# 配置
DEFAULT_GROUP = "Demo Test Group"
GROUP_CHAT_ID = "oc_837f7a5642469ab235750f1bec94414f"

def parse_natural_language(text: str) -> dict:
    """
    本地简单解析（备用，如果 OpenClaw 解析失败）
    提取时间、人物、主题
    """
    text_lower = text.lower()
    
    # 默认参数
    params = {
        "topic": "Meeting",
        "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "time": "15:00",
        "group_name": DEFAULT_GROUP,
        "attendees": [],
        "location": "TBD",
        "duration": 60
    }
    
    # 提取主题（简单规则）
    if "meeting" in text_lower:
        params["topic"] = "Meeting"
    elif "review" in text_lower:
        params["topic"] = "Project Review"
    elif "discuss" in text_lower:
        params["topic"] = "Discussion"
    
    # 提取时间
    if "tomorrow" in text_lower:
        params["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "today" in text_lower:
        params["date"] = datetime.now().strftime("%Y-%m-%d")
    
    # 提取具体时间 (3pm, 15:00, etc)
    import re
    time_match = re.search(r'(\d{1,2})\s*(pm|am)?', text_lower)
    if time_match:
        hour = int(time_match.group(1))
        if time_match.group(2) == 'pm' and hour != 12:
            hour += 12
        params["time"] = f"{hour:02d}:00"
    
    # 提取人名（大写开头的单词，简单规则）
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    # 过滤常见非人名
    non_names = {"Meeting", "Tomorrow", "Today", "Schedule", "Room", "Demo", "Test", "Group"}
    attendees = [w for w in words if w not in non_names]
    if attendees:
        params["attendees"] = attendees
    
    # 提取地点（after "in" or "at" + Room/Location）
    location_match = re.search(r'(?:in|at)\s+(Room\s+\w+|[^\s]+)', text, re.IGNORECASE)
    if location_match:
        params["location"] = location_match.group(1)
    
    return params

def send_via_skill(params: dict) -> bool:
    """
    直接调用 feishu_meeting skill（最可靠方式）
    """
    print("📨 调用 Feishu Meeting Skill...")
    
    skill_path = "/home/seeed/.openclaw/skills/feishu_meeting"
    json_params = json.dumps(params, ensure_ascii=False)
    
    try:
        result = subprocess.run(
            ["python3", "send_meeting_card.py"],
            input=json_params,
            cwd=skill_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            if response.get("success"):
                print(f"✅ 会议卡片发送成功！")
                print(f"   消息ID: {response.get('message_id', 'N/A')}")
                print(f"   发送至: {params['group_name']}")
                return True
            else:
                print(f"❌ Skill 返回错误: {response.get('error')}")
                return False
        else:
            print(f"❌ Skill 执行失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 调用 Skill 异常: {e}")
        return False

def send_via_openclaw_agent(text: str) -> bool:
    """
    尝试通过 OpenClaw Agent 调用（让 Moonshot 解析意图）
    注意：可能仍会使用内置 message 工具而不是我们的 skill
    """
    print("🤖 尝试通过 OpenClaw Agent 处理...")
    
    try:
        # 使用 agent --message --to 格式
        cmd = [
            "openclaw", "agent",
            "--message", text,
            "--to", GROUP_CHAT_ID
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"OpenClaw 输出: {result.stdout}")
        if result.stderr:
            print(f"OpenClaw 日志: {result.stderr}")
        
        # 检查是否成功（通过输出判断）
        if "messageId" in result.stdout or "成功" in result.stdout:
            return True
        return False
        
    except Exception as e:
        print(f"⚠️ OpenClaw Agent 失败: {e}")
        return False

def main():
    """主流程"""
    print("=" * 60)
    print("🎙️ Moltbot Voice Meeting Assistant")
    print("   语音输入 → 智能解析 → 飞书卡片")
    print("=" * 60)
    
    # 1. 录音识别
    print("\n🎤 请用英语说出会议指令...")
    print("   示例: 'Schedule a meeting with Asen tomorrow at 3pm in Room 1'")
    print("   或中文: '明天下午3点跟Tom开会'\n")
    
    try:
        asr = RespeakerASR()
        text, _ = asr.listen_and_recognize(duration=5)
        
        if not text:
            print("❌ 未能识别语音，请重试")
            return
        
        print(f"📝 识别结果: {text}")
        print("-" * 60)
        
        # 2. 解析参数（本地快速解析）
        print("🔍 解析会议信息...")
        params = parse_natural_language(text)
        print(f"   主题: {params['topic']}")
        print(f"   时间: {params['date']} {params['time']}")
        print(f"   参与人: {', '.join(params['attendees']) if params['attendees'] else '待定'}")
        print(f"   地点: {params['location']}")
        
        # 3. 发送会议卡片（直接调用 Skill，最可靠）
        print(f"\n📅 正在发送会议卡片到 {params['group_name']}...")
        
        # 优先使用直接 Skill 调用（确保使用我们的交互式卡片）
        success = send_via_skill(params)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ 完成！请检查飞书群组查看交互式卡片")
            print("   卡片包含：会议详情 + 一键创建日程按钮")
            print("=" * 60)
        else:
            print("\n❌ 发送失败，请检查网络和配置")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()