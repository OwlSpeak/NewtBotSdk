# OwlSpeak Bot 开放平台与 SDK

OwlSpeak 为机器人提供独立的开放 API 平面（`/bot-api/v1`），配套 JavaScript / Python / Go 三种语言的官方 SDK。
机器人不需要注册用户账号、不需要操作客户端：由管理员在控制台创建机器人并签发 **bot token**，
即可在被赋予的角色权限范围内，调用与 **Discord 开放平台 Bot 对齐** 的能力集。

## 设计原则（与 Discord 对齐）

1. **bot 即成员**：`User(IsBot=true)` + `Member` + `Role`，权限位与人类成员同一套 RBAC。
2. **无特权通道**：所有写操作在 handler 内校验权限位与角色层级；安装 bot ≠ 全服管理员。
3. **能力面 = 产品已实现的 Discord Bot 能力**：OwlSpeak 已有的业务 API 均投影到 bot 平面；尚未产品化的能力（如 Webhook、Slash Command、Pin、Thread）明确标注「未实现」。

## 快速开始

1. 管理控制台 → 「开放平台 / 机器人」→ 创建机器人；
2. 「token 管理」→ 签发 token（明文形如 `owlbot_xxx`，仅显示一次）；
3. 「安装到服务器与权限赋予」→ 选择服务器安装，并为机器人绑定角色（按需授予 `MANAGE_ROLES` / `KICK_MEMBERS` / `BAN_MEMBERS` 等）；
4. 用任一 SDK 或直接调 HTTP API 开始工作。

```text
认证方式：HTTP 头 Authorization: Bot <token>   （也兼容 Bearer <token>）
基础地址：https://<你的服务器>/bot-api/v1
限   流：每 bot 20 QPS（突发 40），超限返回 429
```

## Discord 能力对照矩阵

| Discord 领域 | OwlSpeak bot 状态 | 权限位 / 说明 |
|---|---|---|
| Get Current User / Guilds | ✅ | 成员即可读 |
| Get/Modify Guild | ✅ | 修改需 `MANAGE_GUILD` |
| Guild Icon / Banner | ✅ | `MANAGE_GUILD` |
| Channel list / get / create / modify / delete / reorder | ✅ | 创建/改/删需 `MANAGE_CHANNELS`；可见性 `VIEW_CHANNEL` |
| Channel permission overwrites | ✅ | `MANAGE_ROLES` |
| Roles CRUD + member roles | ✅ | `MANAGE_ROLES` + 层级 |
| Messages CRUD / reactions / typing / attachments / search | ✅ | 文本频道对应位；卡片 + 流式为 Owl 扩展 |
| Kick / Ban / Unban / list bans | ✅ | `KICK_MEMBERS` / `BAN_MEMBERS` + 层级 |
| Modify Member (nick) | ✅ | `CHANGE_NICKNAME` / `MANAGE_NICKNAMES` |
| Leave Guild | ✅ | `DELETE .../members/@me` |
| Invites create / list / delete | ✅ | `CREATE_INSTANT_INVITE` 或 `MANAGE_GUILD` |
| Timeout / Moderate | ✅ Restriction API | `MODERATE_MEMBERS` |
| Audit Log | ✅ | `VIEW_AUDIT_LOG` |
| Voice connect / self mute | ✅ | `CONNECT` / `SPEAK` 等投影 caps |
| Voice disconnect / move / server mute·deafen | ✅ | `MOVE_MEMBERS` / `MUTE_MEMBERS` / `DEAFEN_MEMBERS` |
| Stage (apply / bring up·down / queue) | ✅ | `STAGE_*` / `REQUEST_TO_SPEAK` |
| Screen share start/stop | ✅ | `STREAM` / `STREAM_END_OTHERS` |
| Emoji / Sticker | ✅ 贴图包体系 | 自建包 + 服 ban（`MANAGE_EXPRESSIONS` 等） |
| Gateway events | ✅ | 与用户端同事件集，按可见性过滤 |
| Webhooks | ❌ 产品未实现 | 权限位 `MANAGE_WEBHOOKS` 预留 |
| Slash Commands / Interactions | ❌ 产品未实现 | 权限位 `USE_APPLICATION_COMMANDS` 预留 |
| Message Pin / Thread | ❌ 消息二期 | — |
| Guild scheduled events | ❌ 未实现 | — |

## HTTP API 一览

### 基础资源

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/me` | 机器人档案与用户身份 |
| GET | `/guilds` | 已安装的服务器列表 |
| GET | `/guilds/{gid}` | 服务器详情（`member_count` / banners） |
| PATCH | `/guilds/{gid}` | 修改服务器（`MANAGE_GUILD`） |
| GET | `/guilds/{gid}/channels` | 可见频道列表 |
| GET | `/guilds/{gid}/channels/{cid}` | 单频道（guild 前缀） |
| GET | `/channels/{cid}` | 单频道（顶级） |
| POST | `/guilds/{gid}/channels` | 创建频道 |
| PATCH | `/channels/{cid}` | 修改频道 |
| DELETE | `/channels/{cid}` | 删除频道 |
| PATCH | `/guilds/{gid}/channels` | 频道排序 |
| GET | `/guilds/{gid}/members` | 成员目录（`role_ids` / `is_bot` / `is_owner`） |
| GET | `/guilds/{gid}/members/{mid}` | 单成员；`mid` 可为 member_id 或 user_id |
| GET | `/guilds/{gid}/permissions/@me` | 服级最终权限位 |
| GET | `/guilds/{gid}/channels/{cid}/permissions/@me` | 频道级权限投影 |

### 角色与权限覆盖

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST | `/guilds/{gid}/roles` | 列表 / 创建 |
| GET/PATCH/DELETE | `/guilds/{gid}/roles/{rid}` | 详情 / 更新 / 删除 |
| PATCH | `/guilds/{gid}/roles` | 批量排序 |
| PUT/DELETE | `/guilds/{gid}/members/{mid}/roles/{rid}` | 赋角 / 摘角 |
| GET/PUT/DELETE | `/guilds/{gid}/channels/{cid}/overwrites/{target}` | 频道覆盖 |

### 成员治理 / 邀请 / Restriction

| 方法 | 路径 | 说明 |
|---|---|---|
| DELETE | `/guilds/{gid}/members/{mid}` | 踢出；`@me` = 退服 |
| PATCH | `/guilds/{gid}/members/{mid}` | 昵称 |
| PUT/DELETE | `/guilds/{gid}/bans/{uid}` | 封禁 / 解封 |
| GET | `/guilds/{gid}/bans` | 封禁列表 |
| POST | `/guilds/{gid}/invites` | 创建邀请 |
| GET | `/guilds/{gid}/invites` | 邀请列表 |
| DELETE | `/invites/{code}` | 撤销邀请 |
| GET | `/invites/{code}` | 邀请预览 |
| POST/GET/PATCH/DELETE | `/guilds/{gid}/restrictions[/{id}]` | Restriction（Timeout） |

### 消息

| 方法 | 路径 | 说明 |
|---|---|---|
| POST/GET | `/channels/{cid}/messages` | 发消息 / 拉历史 |
| GET/PATCH/DELETE | `/channels/{cid}/messages/{mid}` | 详情 / 编辑 / 删除 |
| PUT/DELETE | `.../reactions/{emoji}/@me` | 反应 |
| GET | `.../reactions/{emoji}` | 反应者列表 |
| POST | `/channels/{cid}/typing` | 打字指示 |
| POST | `/channels/{cid}/attachments/presign` | 附件预签名 |
| GET | `/search/messages?q=` | 搜索 |
| POST | `/channels/{cid}/messages/stream` … | 流式三段协议（Owl 扩展） |

### 语音 / 舞台

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/voice/join` `/leave` `/refresh-token` | 进房 / 离房 / 续签 |
| PATCH | `/voice/state` | 自身静音闭听 |
| GET | `/guilds/{gid}/channels/{cid}/voice-states` | 频道语音状态 |
| POST | `/guilds/{gid}/voice/disconnect` | 踢出语音 |
| POST | `/guilds/{gid}/voice/move` | 移动成员 |
| PATCH | `/guilds/{gid}/voice/states/{uid}` | 服务器静音/闭听 |
| GET/PATCH | `/channels/{cid}/voice-stage` | 舞台配置 |
| POST | `/channels/{cid}/stage/apply` 等 | 申请/抱麦/下麦 |
| POST | `/channels/{cid}/voice/screen/start` 等 | 屏幕共享 |

### 审计 / 贴图

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/guilds/{gid}/audit-logs` | 本服审计 |
| * | `/users/@me/sticker-packs` 等 | 贴图包 / 库 / 可用集合 |
| GET/PUT/DELETE | `/guilds/{gid}/sticker-pack-bans/{pack}` | 服 ban |

### Gateway

```text
WS  wss://<服务器>/bot-api/v1/gateway
S→C HELLO → C→S IDENTIFY{token} → S→C READY
C→S HEARTBEAT ←→ HEARTBEAT_ACK
S→C DISPATCH {t, d}
```

事件与用户端一致（按频道可见性过滤），含：
`MESSAGE_*`、`MESSAGE_REACTION_*`、`MESSAGE_STREAM_*`、`TYPING_START`、
`GUILD_*`、`GUILD_MEMBER_*`、`GUILD_ROLE_*`、`CHANNEL_*`、`PERMISSIONS_UPDATE`、
`VOICE_STATE_UPDATE`、`VOICE_CAPS_UPDATE` 等。

反应事件载荷：

```json
{
  "message_id": "1234567890",
  "channel_id": "<uuid>",
  "guild_id": "<uuid>",
  "user_id": "<uuid>",
  "emoji": "✅"
}
```

### 反应角色 / 验证门示例

```js
const gw = bot.connectGateway()
gw.on("MESSAGE_REACTION_ADD", async (ev) => {
  if (String(ev.message_id) !== RULES_MESSAGE_ID || ev.emoji !== "✅") return
  await bot.addMemberRole(ev.guild_id, ev.user_id, VERIFIED_ROLE_ID)
})
```

需给 bot 绑定带 `MANAGE_ROLES` 的角色，且层级高于「已验证」角色。

### 卡片（card）载荷

服务端只校验「JSON 对象、≤8KB」。推荐结构：

```json
{
  "title": "部署完成",
  "description": "版本 v1.4.2 已发布",
  "color": "#22c55e",
  "fields": [{ "name": "耗时", "value": "42s", "inline": true }],
  "footer": "CI Bot"
}
```

## 管理 API（后台 `/api/v1`，管理员 JWT）

`POST/GET/PATCH/DELETE /bots`、`POST/GET/DELETE /bots/{id}/tokens`、
`GET/PUT/DELETE /guilds/{gid}/bots/{botID}`（安装/卸载，需 `MANAGE_BOTS`）。

## 常用权限位（uint64）

| 位 | 常量 | 值 |
|---|---|---|
| 1 | `KICK_MEMBERS` | `1<<1` |
| 2 | `BAN_MEMBERS` | `1<<2` |
| 4 | `MANAGE_CHANNELS` | `1<<4` |
| 5 | `MANAGE_GUILD` | `1<<5` |
| 10 | `VIEW_CHANNEL` | `1<<10` = 1024 |
| 11 | `SEND_MESSAGES` | `1<<11` |
| 13 | `MANAGE_MESSAGES` | `1<<13` |
| 20 | `CONNECT` | `1<<20` |
| 28 | `MANAGE_ROLES` | `1<<28` |
| 39 | `MODERATE_MEMBERS` | `1<<39` |

完整列表见 `backend/internal/rbac/permissions.go`。

## SDK 覆盖说明

四语言 SDK 均覆盖本文件列出的 **bot 平面** 端点（见 [COVERAGE.md](./COVERAGE.md)），包括：

- 服务器 / 频道 / 角色 / 权限覆盖 / 图标横幅  
- 成员治理 / 邀请 / Restriction / 审计  
- 消息、反应、已读 ack、附件 presign、搜索、流式  
- 入场语音包、语音进房与管理、舞台与屏幕共享  
- 贴图包 / 库 / 服 ban  
- Gateway  

各语言另提供底层通用请求（Go `Raw`、JS `request`、Rust `raw`、Python `_request`）以兼容未来新增端点。

## SDK

| 语言 | 目录 | 说明 |
|---|---|---|
| JavaScript / TypeScript | [`../javascript/`](../javascript/) | 零依赖（Node ≥ 21） |
| Python | [`../python/`](../python/) | 标准库 REST；Gateway 可选 `websockets` |
| Go | [`../go/`](../go/) | Gateway + 可接 pion 语音 |
| Rust | [`../rust/`](../rust/) | 异步 REST + Gateway |

各目录内含完整 README 与示例。
