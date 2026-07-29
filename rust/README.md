# newtspeak-bot（Rust SDK）

NewtSpeak 机器人开放平台官方 Rust SDK。异步 REST（`reqwest` + `tokio`）与 Gateway（`tokio-tungstenite`）。

## 安装

```toml
[dependencies]
newtspeak-bot = { git = "https://github.com/NewtSpeak/NewtBotSdk", path = "rust" }
# 或本地路径：
# newtspeak-bot = { path = "../rust" }
tokio = { version = "1", features = ["rt-multi-thread", "macros"] }
serde_json = "1"
```

## 快速上手

```rust
use newtspeak_bot::{connect_gateway, Client, HandlerMap};
use serde_json::json;

#[tokio::main]
async fn main() -> newtspeak_bot::Result<()> {
    let bot = Client::new("https://newt.example.com", std::env::var("NEWT_BOT_TOKEN").unwrap())?;

    bot.send_text("channel-id", "你好！").await?;
    bot.send_card(
        "channel-id",
        json!({ "title": "部署完成", "color": "#22c55e" }),
    )
    .await?;

    // 流式回复
    let (stream_id, _) = bot.start_stream("channel-id", "思考中：").await?;
    bot.stream_append("channel-id", &stream_id, "答案是 42。").await?;
    bot.stream_end("channel-id", &stream_id, None).await?;

    // 反应角色
    let handlers = HandlerMap::new();
    let bot2 = bot.clone();
    handlers
        .on("MESSAGE_REACTION_ADD", move |_, ev| {
            let bot = bot2.clone();
            tokio::spawn(async move {
                let emoji = ev.get("emoji").and_then(|v| v.as_str()).unwrap_or("");
                if emoji != "✅" {
                    return;
                }
                let guild = ev.get("guild_id").and_then(|v| v.as_str()).unwrap_or("");
                let user = ev.get("user_id").and_then(|v| v.as_str()).unwrap_or("");
                let _ = bot
                    .add_member_role(guild, user, "verified-role-id")
                    .await;
            });
        })
        .await;

    let gw = connect_gateway(bot, handlers).await?;
    // 保持运行…
    tokio::signal::ctrl_c().await.ok();
    gw.close().await;
    Ok(())
}
```

## 按钮交互与 ephemeral

```rust
use newtspeak_bot::{connect_gateway, Client, HandlerMap, Interaction};
use serde_json::json;

// 1. 发带交互按钮的卡片（custom_id 触发 INTERACTION_CREATE；url 为链接按钮）
bot.send_card(
    "channel-id",
    json!({
        "title": "发布 v1.4.2？",
        "buttons": [
            { "label": "批准", "custom_id": "approve:42", "style": "success" },
            { "label": "查看日志", "url": "https://ci.example.com/run/42" }
        ]
    }),
)
.await?;

// 2. ephemeral 消息：仅指定用户 + bot 自己可见（card 可为 None）
bot.send_ephemeral("channel-id", "user-id", "只有你能看到这条提示", None)
    .await?;

// 3. 处理按钮点击（15 分钟内回应；reply 的 ephemeral 传 None 即服务端默认 true）
let handlers = HandlerMap::new();
handlers
    .on_interaction(bot.clone(), |interaction: Interaction| {
        tokio::spawn(async move {
            if interaction.custom_id == "approve:42" {
                let _ = interaction
                    .update_message(None, Some(json!({ "title": "已批准 ✅" })))
                    .await;
            } else {
                let _ = interaction.reply("已驳回", None, None).await; // 仅点击者可见
            }
            // 耗时任务可先 interaction.ack().await，稍后再 reply / update_message 一次（defer 模式）
        });
    })
    .await;
let gw = connect_gateway(bot.clone(), handlers).await?;
```

## API 摘要

| 领域 | 方法 |
|------|------|
| 资源 | `me` / `guilds` / `guild` / `channels` / `channel` / `members` / `member` / `permissions` |
| 角色 | `roles` / `create_role` / `add_member_role` / `remove_member_role` |
| 覆盖 | `overwrites` / `set_overwrite` / `delete_overwrite` |
| 治理 | `kick_member` / `leave_guild` / `ban_user` / `create_invite` / `create_restriction` / `audit_logs` |
| 消息 | `send_message` / `send_text` / `send_card` / `send_ephemeral` / `get_messages` / `add_reaction` / `typing` |
| 流式 | `start_stream` → `stream_append` → `stream_end` |
| 交互 | `HandlerMap::on_interaction` / `Interaction::from_value` → `ack` / `reply` / `update_message` |
| 语音 | `join_voice` / `leave_voice` / `refresh_voice_token` / `voice_move` |
| 事件 | `connect_gateway` + `HandlerMap::on` |

完整 HTTP 协议见 [`../docs/API.md`](../docs/API.md)。
