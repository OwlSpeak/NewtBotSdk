# Bot API ↔ SDK 覆盖清单

对照 Owl-Server `/bot-api/v1` 挂载面（`botapi.RegisterBotAPI` 及各 `RegisterBot`）。

图例：✅ 已封装 · ⚠️ 经 `request`/`raw` 可调用 · ❌ 不在 bot 平面

| 领域 | 服务端路径 | JS | Go | Python | Rust |
|------|-----------|----|----|--------|------|
| 基础 me/guilds/channels/members | ✅ | ✅ | ✅ | ✅ | ✅ |
| 服务器 GET/PATCH | ✅ | ✅ | ✅ | ✅ | ✅ |
| 图标/横幅 multipart | ✅ | ✅ | ✅ | ✅ | ✅ |
| 多 banner 列表 CRUD | ✅ | ✅ | ✅ | ✅ | ✅ |
| 频道 CRUD/排序/解锁 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 角色 CRUD/排序/赋角 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 权限覆盖 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 踢/封/昵称/退服 | ✅ | ✅ | ✅ | ✅ | ✅ |
| name-style | ✅ | ✅ | ✅ | ✅ | ✅ |
| 邀请 create/list/delete/preview | ✅ | ✅ | ✅ | ✅ | ✅ |
| Restriction 全套 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 审计日志 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 消息 CRUD/反应/打字/搜索 | ✅ | ✅ | ✅ | ✅ | ✅ |
| ephemeral 消息（visible_to_user_ids） | ✅ | ✅ | ✅ | ✅ | ✅ |
| 按钮交互（INTERACTION_CREATE + callback） | ✅ | ✅ | ✅ | ✅ | ✅ |
| 消息编辑历史 / ack / 已读 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 附件 presign/upload-limit | ✅ | ✅ | ✅ | ✅ | ✅ |
| 流式消息 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 入场语音包 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 语音进房/管理/节点 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 舞台 + 屏幕共享 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 贴图包/库/服 ban | ✅ | ✅ | ✅ | ✅ | ✅ |
| Gateway | ✅ | ✅ | ✅ | ✅ | ✅ |
| 后台创建 bot/token（/api/v1） | ❌ 非 bot token | — | — | — | — |

## 按钮交互 / ephemeral 各语言新方法

| 能力 | JS | Go | Python | Rust |
|------|----|----|--------|------|
| ephemeral 发送 | `sendEphemeral` · `sendMessage({visibleToUserIds})` | `SendEphemeral` · `SendMessageOptions.VisibleToUserIDs` | `send_ephemeral` · `send_message(visible_to_user_ids=...)` | `send_ephemeral` · `send_message` 带 `visible_to_user_ids` |
| 交互事件订阅 | `gw.on("interaction", handler)` | `gw.OnInteraction(func(*Interaction))` | `on_event("interaction", interaction)` 包装回调 | `HandlerMap::on_interaction(client, handler)` |
| 交互对象与回应 | `Interaction`：`ack()` / `reply()` / `updateMessage()` | `Interaction`：`Ack` / `Reply` / `ReplyText` / `UpdateMessage`（`Client.ParseInteraction` 解析） | `Interaction`：`ack()` / `reply()` / `update_message()` | `Interaction`：`ack` / `reply` / `update_message`（`Interaction::from_value` 解析） |

最后校验：与 `internal/botapi/register.go` 挂载模块同步。
