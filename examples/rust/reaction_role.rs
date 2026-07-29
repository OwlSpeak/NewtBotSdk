//! 反应角色最小示例（作为文档参考；可拷贝到独立 binary crate）。
//!
//! 运行需自行建 package 并依赖 path = "../../rust"。

use newtspeak_bot::{connect_gateway, Client, HandlerMap};
use std::sync::Arc;

#[tokio::main]
async fn main() -> newtspeak_bot::Result<()> {
    let bot = Client::new(
        std::env::var("NEWT_BASE_URL").expect("NEWT_BASE_URL"),
        std::env::var("NEWT_BOT_TOKEN").expect("NEWT_BOT_TOKEN"),
    )?;
    let rules = Arc::new(std::env::var("RULES_MESSAGE_ID").expect("RULES_MESSAGE_ID"));
    let role = Arc::new(std::env::var("VERIFIED_ROLE_ID").expect("VERIFIED_ROLE_ID"));

    let handlers = HandlerMap::new();
    let bot_c = bot.clone();
    let rules_c = rules.clone();
    let role_c = role.clone();
    handlers
        .on("MESSAGE_REACTION_ADD", move |_, ev| {
            let bot = bot_c.clone();
            let rules = rules_c.clone();
            let role = role_c.clone();
            tokio::spawn(async move {
                let mid = ev.get("message_id").map(|v| v.to_string()).unwrap_or_default();
                let emoji = ev.get("emoji").and_then(|v| v.as_str()).unwrap_or("");
                if mid.trim_matches('"') != rules.as_str() || emoji != "✅" {
                    return;
                }
                let guild = ev.get("guild_id").and_then(|v| v.as_str()).unwrap_or("");
                let user = ev.get("user_id").and_then(|v| v.as_str()).unwrap_or("");
                if let Err(e) = bot.add_member_role(guild, user, role.as_str()).await {
                    eprintln!("赋角失败: {e}");
                } else {
                    println!("已赋角 {user}");
                }
            });
        })
        .await;

    let _gw = connect_gateway(bot, handlers).await?;
    tokio::signal::ctrl_c().await.ok();
    Ok(())
}
