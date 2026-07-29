//! NewtSpeak 机器人开放平台官方 Rust SDK。
//!
//! # 快速开始
//!
//! ```no_run
//! use newtspeak_bot::{Client, HandlerMap, connect_gateway};
//! use serde_json::json;
//!
//! #[tokio::main]
//! async fn main() -> newtspeak_bot::Result<()> {
//!     let bot = Client::new("https://newt.example.com", "newtbot_xxx")?;
//!
//!     // 发卡片消息
//!     bot.send_card(
//!         "channel-uuid",
//!         json!({ "title": "部署完成", "color": "#22c55e" }),
//!     )
//!     .await?;
//!
//!     // Gateway 实时事件
//!     let handlers = HandlerMap::new();
//!     handlers
//!         .on("MESSAGE_REACTION_ADD", |_, payload| {
//!             println!("反应: {payload}");
//!         })
//!         .await;
//!     let gw = connect_gateway(bot.clone(), handlers).await?;
//!     // ...
//!     gw.close().await;
//!     Ok(())
//! }
//! ```
//!
//! 认证：`Authorization: Bot <token>`；基础地址自动拼接 `/bot-api/v1`。
//! 协议细节见仓库根目录 [`docs/API.md`](../docs/API.md)。

mod client;
mod error;
mod gateway;
mod interaction;

pub use client::Client;
pub use error::{Error, Result};
pub use gateway::{connect as connect_gateway, EventHandler, Gateway, HandlerMap};
pub use interaction::{Interaction, InteractionMember};
