# NewtBotSdk 接口调用文档

Base：`https://<server>/bot-api/v1`  
认证：`Authorization: Bot <newtbot_xxx>`（兼容 `Bearer`）

完整矩阵与 schema 见 [API.md](./API.md)。

## 认证与约定

```http
GET /bot-api/v1/me HTTP/1.1
Host: newt-panel.example.com
Authorization: Bot newtbot_xxx
Accept: application/json
```

| 项 | 值 |
|----|-----|
| 限流 | 20 QPS / bot，突发 40 → `429` |
| ID | 雪花或 UUID 字符串；成员路径同时接受 `member_id` / `user_id` |
| 错误体 | 通常 `{ "error": { "code", "message" } }` |

### curl 速查

```bash
export BASE=https://newt-panel.example.com/bot-api/v1
export AUTH="Authorization: Bot $NEWT_BOT_TOKEN"

curl -sH "$AUTH" $BASE/me
curl -sH "$AUTH" $BASE/guilds
curl -sH "$AUTH" -H 'Content-Type: application/json' \
  -d '{"content":"hello"}' $BASE/channels/$CID/messages
```

### SDK 底层通用请求

| 语言 | 方法 |
|------|------|
| Go | `bot.Raw(method, path, body)` |
| JS | `bot.request(method, path, body?)` |
| Python | `bot._request(method, path, body=…)` |
| Rust | `bot.raw(method, path, body).await` |

---

## HTTP 一览

### 基础

| 方法 | 路径 | SDK 示例 |
|------|------|----------|
| GET | `/me` | `Me()` / `me()` |
| GET | `/guilds` | `Guilds()` |
| GET/PATCH | `/guilds/{gid}` | `Guild` / `UpdateGuild` |
| GET | `/guilds/{gid}/channels` | `Channels` |
| GET | `/channels/{cid}` | `Channel` |
| POST | `/guilds/{gid}/channels` | `CreateChannel` |
| PATCH/DELETE | `/channels/{cid}` | `UpdateChannel` / `DeleteChannel` |
| PATCH | `/guilds/{gid}/channels` | `ReorderChannels` |
| GET | `/guilds/{gid}/members[/{mid}]` | `Members` / `Member` |
| GET | `/guilds/{gid}/permissions/@me` | `Permissions` |
| GET | `…/channels/{cid}/permissions/@me` | `ChannelPermissions` |

### 角色 / 覆盖

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/guilds/{gid}/roles` | 列表 / 创建 |
| GET/PATCH/DELETE | `/guilds/{gid}/roles/{rid}` | 详情 / 改 / 删 |
| PATCH | `/guilds/{gid}/roles` | 批量排序 |
| PUT/DELETE | `/guilds/{gid}/members/{mid}/roles/{rid}` | 赋角 / 摘角 |
| GET/PUT/DELETE | `…/channels/{cid}/overwrites/{target}` | 权限覆盖 |

### 成员治理 / 邀请 / Restriction

| 方法 | 路径 | 权限 |
|------|------|------|
| DELETE | `/guilds/{gid}/members/{mid}` | 踢；`@me` = 退服 |
| PATCH | `/guilds/{gid}/members/{mid}` | 昵称 |
| PUT/DELETE | `/guilds/{gid}/bans/{uid}` | 封 / 解封 |
| GET | `/guilds/{gid}/bans` | 封禁列表 |
| POST/GET | `/guilds/{gid}/invites` | 创建 / 列表 |
| GET/DELETE | `/invites/{code}` | 预览 / 撤销 |
| * | `/guilds/{gid}/restrictions[/{id}]` | Timeout 类限制 |

### 消息

| 方法 | 路径 | 说明 |
|------|------|------|
| POST/GET | `/channels/{cid}/messages` | 发 / 历史 |
| GET/PATCH/DELETE | `…/messages/{mid}` | 详情 / 编辑 / 删 |
| PUT/DELETE | `…/reactions/{emoji}/@me` | 反应 |
| GET | `…/reactions/{emoji}` | 反应者 |
| POST | `/channels/{cid}/typing` | 打字 |
| POST | `/channels/{cid}/attachments/presign` | 附件预签 |
| GET | `/search/messages?q=` | 搜索 |
| POST | `/channels/{cid}/messages/stream` … | 流式三段（Owl） |
| POST | `/interactions/{id}/callback` | 按钮回应 |

**发消息 body：**

```json
{
  "content": "文本",
  "card": { "title": "…", "buttons": [/* 见下 */] },
  "reply_to_id": null,
  "attachment_ids": [],
  "visible_to_user_ids": ["<uuid>"]
}
```

- `visible_to_user_ids`：ephemeral（≤20）；**不可带附件**
- `card`：JSON 对象，≤8KB（`buttons` 另计规则）

**按钮 `card.buttons[]`（≤25）：**

| 字段 | 约束 |
|------|------|
| `label` | 1–40 字，必填 |
| `url` **或** `custom_id` | 互斥必居其一 |
| `custom_id` | `[A-Za-z0-9_\-:.]` 1–64，消息内唯一 |
| `style` | `primary` / `secondary` / `success` / `danger` |
| `size` | `xs` / `sm` / `md` / `lg` |
| `row` | 0–4 |
| `visible_to` | `{users≤20, roles≤10}` |

### 交互 callback

```http
POST /bot-api/v1/interactions/{interactionID}/callback
Authorization: Bot <token>
```

```json
{
  "token": "newtint_...",
  "type": "ack | reply | update_message",
  "content": "可选",
  "card": {},
  "ephemeral": true
}
```

| type | 语义 |
|------|------|
| `ack` | 停转圈；之后可再 `reply`/`update_message` 一次 |
| `reply` | 频道新消息；`ephemeral` 默认 true |
| `update_message` | 改原消息 content/card |

| HTTP | 含义 |
|------|------|
| 404 | token 不符 / 非本 bot |
| 410 | 超过 15 分钟 |
| 409 | 已回应（含 defer 上限） |

### 语音 / 舞台 / 屏幕

| 方法 | 路径 |
|------|------|
| POST | `/voice/join` `/leave` `/refresh-token` |
| PATCH | `/voice/state` |
| GET | `/guilds/{gid}/channels/{cid}/voice-states` |
| POST | `/guilds/{gid}/voice/disconnect` `/move` |
| PATCH | `/guilds/{gid}/voice/states/{uid}` |
| GET/PATCH | `/channels/{cid}/voice-stage` |
| POST | `/channels/{cid}/stage/*`、`/voice/screen/*` |

`POST /voice/join` 返回 Media Token + `advertise_wss_url`，媒体走 SFU（不经 bot-api）。

### 审计 / 贴图

| 方法 | 路径 |
|------|------|
| GET | `/guilds/{gid}/audit-logs` |
| * | `/users/@me/sticker-packs` 等 |
| GET/PUT/DELETE | `/guilds/{gid}/sticker-pack-bans/{pack}` |

---

## Gateway

```text
WS  wss://<server>/bot-api/v1/gateway

S→C  HELLO
C→S  IDENTIFY { "token": "newtbot_..." }
S→C  READY
C↔S  HEARTBEAT / HEARTBEAT_ACK
S→C  DISPATCH { "t": "<EVENT>", "d": { ... } }
```

### 常用事件 `t`

| 事件 | 用途 |
|------|------|
| `MESSAGE_CREATE` / `UPDATE` / `DELETE` | 消息 |
| `MESSAGE_REACTION_ADD` / `REMOVE` | 反应角色 |
| `MESSAGE_STREAM_*` | 流式 |
| `TYPING_START` | 打字 |
| `GUILD_*` / `GUILD_MEMBER_*` / `GUILD_ROLE_*` | 服/成员/角色 |
| `CHANNEL_*` / `PERMISSIONS_UPDATE` | 频道与权限 |
| `VOICE_STATE_UPDATE` / `VOICE_CAPS_UPDATE` | 语音 |
| `INTERACTION_CREATE` | 按钮点击（bot 专属） |

**反应载荷：**

```json
{
  "message_id": "…",
  "channel_id": "…",
  "guild_id": "…",
  "user_id": "…",
  "emoji": "✅"
}
```

**交互载荷：**

```json
{
  "id": "…",
  "token": "newtint_…",
  "guild_id": "…",
  "channel_id": "…",
  "message_id": "…",
  "custom_id": "approve:42",
  "member": { "user_id": "…", "username": "alice", "roles": [] },
  "expires_at": "2026-07-26T12:15:00Z"
}
```

---

## 管理面（非 bot token）

创建机器人 / 签 token / 安装到服，走管理员 JWT：

```text
/api/v1/bots
/api/v1/bots/{id}/tokens
/api/v1/guilds/{gid}/bots/{botID}    # 安装需 MANAGE_BOTS
```

SDK **不**覆盖该面；用控制台或 Agent（system_admin）操作。

---

## 常用权限位（uint64）

| 位 | 常量 | 值 |
|----|------|-----|
| 1 | `KICK_MEMBERS` | `1<<1` |
| 2 | `BAN_MEMBERS` | `1<<2` |
| 4 | `MANAGE_CHANNELS` | `1<<4` |
| 5 | `MANAGE_GUILD` | `1<<5` |
| 10 | `VIEW_CHANNEL` | `1<<10` |
| 11 | `SEND_MESSAGES` | `1<<11` |
| 13 | `MANAGE_MESSAGES` | `1<<13` |
| 20 | `CONNECT` | `1<<20` |
| 28 | `MANAGE_ROLES` | `1<<28` |
| 39 | `MODERATE_MEMBERS` | `1<<39` |

完整列表：`Newt-Server/backend/internal/rbac/permissions.go`。

---

## 语言方法映射（摘要）

| 能力 | Go | JS | Python | Rust |
|------|----|----|--------|------|
| 发文本 | `SendText` | `sendText` | `send_message` | `send_text` |
| 卡片 | `SendCard` | `sendCard` | `send_card` | `send_card` |
| ephemeral | `SendEphemeral` | `sendEphemeral` | `send_ephemeral` | `send_ephemeral` |
| 流式 | `StartStream` | `startStream` | — | — |
| 赋角 | `AddMemberRole` | `addMemberRole` | `add_member_role` | `add_member_role` |
| Gateway | `ConnectGateway` | `connectGateway` | `run_gateway` | HandlerMap |
| 交互 | `OnInteraction` | `on("interaction")` | event wrapper | `on_interaction` |
| 进语音 | `JoinVoice` | `joinVoice` | `join_voice` | `join_voice` |

Go 全方法目录：[METHODS.md](./METHODS.md)。

---

## 能力边界（未实现）

| 能力 | 状态 |
|------|------|
| Webhooks | ❌ |
| Slash Commands | ❌（按钮交互已支持） |
| Pin / Thread | ❌ |
| Guild 日程 | ❌ |
