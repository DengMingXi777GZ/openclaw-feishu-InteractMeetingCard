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

### 通过命令行
```bash
# 直接调用
python3 send_meeting_card.py

# 带参数
python3 send_meeting_card.py '{"topic": "周会", "time": "14:00"}'

# 管道输入
echo '{"topic": "讨论", "date": "2024-01-20"}' | python3 send_meeting_card.py
```

## 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| topic | string | 否 | 会议主题，默认"会议" |
| date | string | 否 | 日期(YYYY-MM-DD)，默认明天 |
| time | string | 否 | 时间(HH:MM)，默认15:00 |
| attendees | list | 否 | 参与人列表 |
| location | string | 否 | 会议地点 |
| duration | int | 否 | 会议时长(分钟)，默认60 |
| group_name | string | 否 | 群组名称 |
| group_chat_id | string | 否 | 群组ID，有默认值 |

## 卡片功能

### 交互元素
1. **创建日程按钮** - 一键添加到飞书日历
2. **提醒我按钮** - 设置会议提醒
3. **会议详情** - 时间、地点、参与人

### 视觉设计
- 蓝色主题头部
- 清晰的信息层次
- 响应式布局
- 现代化UI设计

## 错误处理

### 常见错误
```json
{
  "success": false,
  "error": "认证失败: 无效的app_id"
}
```

### 成功响应
```json
{
  "success": true,
  "message_id": "om_1234567890",
  "group": "项目团队"
}
```

## 集成说明

### 在OpenClaw中使用
这个Skill设计为OpenClaw生态的一部分，可以通过以下方式调用：

1. **直接Skill调用** - 最可靠的方式
2. **Agent消息处理** - 通过AI解析意图
3. **命令行工具** - 独立运行

### 认证配置
需要在OpenClaw中配置飞书认证信息：
```json
{
  "feishu": {
    "appId": "cli_xxx",
    "appSecret": "xxx",
    "verificationToken": "xxx",
    "encryptKey": "xxx"
  }
}
```

## 开发扩展

### 自定义卡片样式
修改 `send_meeting_card.py` 中的 `create_meeting_card()` 函数：
- 调整颜色主题
- 添加新按钮
- 修改布局结构

### 添加新功能
- 循环会议支持
- 会议纪要生成
- 视频会议集成
- 日历同步

### 多语言支持
- 国际化消息模板
- 本地化时间格式
- 多语言语音输入

## 最佳实践

### 性能优化
- 缓存常用群组信息
- 批量发送优化
- 错误重试机制

### 安全建议
- 保护API密钥
- 验证输入参数
- 限制发送频率

### 用户体验
- 提供清晰的错误信息
- 支持语音和文本输入
- 实时状态反馈

## 更新日志

### v1.0.0
- ✅ 基础会议卡片功能
- ✅ 交互式按钮支持
- ✅ 一键创建日程
- ✅ 多参数配置
- ✅ 错误处理机制

### 计划功能
- 🔄 循环会议支持
- 🔄 会议纪要
- 🔄 视频会议集成
- 🔄 语音转文字优化

## 技术支持

- GitHub Issues: 报告问题和功能请求
- 文档: 详细API文档和使用指南
- 社区: OpenClaw Discord社区

---

**注意**: 这是OpenClaw生态系统的一部分，需要配合OpenClaw Gateway使用。