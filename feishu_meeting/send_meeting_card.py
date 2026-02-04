#!/usr/bin/env python3
"""
飞书会议卡片发送模块
用于OpenClac Skill系统，创建并发送交互式会议邀请卡片
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 添加到Python路径
try:
    from tools import message
except ImportError:
    # 直接调用模式
    import subprocess
    
    def send_feishu_message(target: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """通过OpenClaw发送飞书消息"""
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

def create_meeting_card(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建飞书交互式会议卡片
    
    支持参数:
    - topic: 会议主题
    - date: 会议日期 (YYYY-MM-DD)
    - time: 会议时间 (HH:MM)
    - attendees: 参与人列表
    - location: 会议地点
    - duration: 会议时长(分钟)
    - group_name: 群组名称
    """
    
    # 默认值处理
    topic = params.get("topic", "会议")
    date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
    time = params.get("time", "15:00")
    attendees = params.get("attendees", [])
    location = params.get("location", "待定")
    duration = params.get("duration", 60)
    group_name = params.get("group_name", "项目组")
    
    # 构建参与人字符串
    attendees_str = ", ".join(attendees) if attendees else "待定"
    
    # 构建日期时间显示
    try:
        meeting_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        date_display = meeting_datetime.strftime("%m月%d日 %H:%M")
        end_time = meeting_datetime + timedelta(minutes=duration)
        time_range = f"{time} - {end_time.strftime('%H:%M')}"
    except:
        date_display = f"{date} {time}"
        time_range = time
    
    # 创建卡片内容
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
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**🕐 时间：** {date_display} ({time_range})"
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
                    "tag": "hr"
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
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "提醒我"
                            },
                            "type": "default",
                            "value": {
                                "action": "set_reminder",
                                "meeting_data": {
                                    "topic": topic,
                                    "datetime": f"{date} {time}"
                                }
                            }
                        }
                    ]
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"💡 点击"创建日程"可直接在飞书日历中添加此会议"
                        }
                    ]
                }
            ]
        }
    }
    
    return card_content

def send_meeting_card(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    发送会议卡片到飞书群组
    
    Args:
        params: 会议参数字典
        
    Returns:
        发送结果字典
    """
    
    try:
        # 创建卡片内容
        card_content = create_meeting_card(params)
        
        # 获取群组ID
        group_chat_id = params.get("group_chat_id", "oc_837f7a5642469ab235750f1bec94414f")
        
        # 发送消息
        result = send_feishu_message(group_chat_id, card_content)
        
        if result.get("success"):
            print(f"✅ 会议卡片发送成功！")
            print(f"   消息ID: {result.get('message_id', 'N/A')}")
            print(f"   发送至: {params.get('group_name', '群组')}")
            return {
                "success": True,
                "message_id": result.get("message_id"),
                "group": params.get("group_name", "群组")
            }
        else:
            error_msg = result.get("error", "未知错误")
            print(f"❌ 发送失败: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
            
    except Exception as e:
        error_msg = f"发送异常: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

def main():
    """主函数 - 支持命令行调用"""
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 从命令行参数读取JSON
        if sys.argv[1] == "--help":
            print("用法:")
            print("  python3 send_meeting_card.py '{\"topic\": \"会议\", \"date\": \"2024-01-15\", \"time\": \"15:00\"}'")
            print("或:")
            print("  echo '{JSON}' | python3 send_meeting_card.py")
            return
            
        json_input = sys.argv[1]
    else:
        # 从标准输入读取JSON
        json_input = sys.stdin.read().strip()
    
    if not json_input:
        # 默认测试数据
        test_params = {
            "topic": "项目评审会议",
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "15:00",
            "attendees": ["张三", "李四", "王五"],
            "location": "会议室A",
            "duration": 60,
            "group_name": "项目团队"
        }
        result = send_meeting_card(test_params)
    else:
        try:
            params = json.loads(json_input)
            result = send_meeting_card(params)
        except json.JSONDecodeError as e:
            result = {
                "success": False,
                "error": f"JSON解析错误: {str(e)}"
            }
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()