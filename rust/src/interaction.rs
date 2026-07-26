//! 按钮交互（Gateway `INTERACTION_CREATE`）支持。

use crate::client::Client;
use crate::error::{Error, Result};
use serde_json::{json, Value};

/// 触发交互的成员信息。
#[derive(Debug, Clone, Default)]
pub struct InteractionMember {
    pub user_id: String,
    pub username: String,
    pub roles: Vec<String>,
}

/// 按钮点击交互（Gateway `INTERACTION_CREATE` 载荷包装）。
///
/// 15 分钟内需用一次性 token 回应：
/// - [`ack`](Self::ack) 仅确认（用户按钮停止转圈）；之后仍可再 reply/update_message 一次（defer 模式）
/// - [`reply`](Self::reply) 以 bot 身份在原频道发新消息，缺省 ephemeral（仅点击者可见）
/// - [`update_message`](Self::update_message) 更新原消息的 card 和/或 content
///
/// 服务端错误：404（token 不符/非本 bot）、410 `INTERACTION_EXPIRED`、409 `ALREADY_RESPONDED`。
#[derive(Clone)]
pub struct Interaction {
    /// 交互 ID（雪花）。
    pub id: String,
    /// 一次性回应令牌（`owlint_...`）。
    pub token: String,
    pub guild_id: String,
    pub channel_id: String,
    /// 按钮所在消息 ID。
    pub message_id: String,
    pub custom_id: String,
    pub member: InteractionMember,
    /// 过期时间（创建 +15 分钟，ISO 字符串）。
    pub expires_at: String,
    /// 原始事件载荷。
    pub raw: Value,
    client: Client,
}

fn str_field(value: &Value, field: &str) -> String {
    value
        .get(field)
        .and_then(|v| v.as_str())
        .unwrap_or_default()
        .to_string()
}

impl Interaction {
    /// 把 `INTERACTION_CREATE` 事件载荷解析为可回应的 Interaction。
    pub fn from_value(client: Client, payload: Value) -> Result<Self> {
        let id = str_field(&payload, "id");
        let token = str_field(&payload, "token");
        if id.is_empty() || token.is_empty() {
            return Err(Error::Invalid("INTERACTION_CREATE 载荷缺少 id/token".into()));
        }
        let member_value = payload.get("member").cloned().unwrap_or(Value::Null);
        let member = InteractionMember {
            user_id: str_field(&member_value, "user_id"),
            username: str_field(&member_value, "username"),
            roles: member_value
                .get("roles")
                .and_then(|v| v.as_array())
                .map(|items| {
                    items
                        .iter()
                        .filter_map(|v| v.as_str().map(str::to_string))
                        .collect()
                })
                .unwrap_or_default(),
        };
        Ok(Self {
            id,
            token,
            guild_id: str_field(&payload, "guild_id"),
            channel_id: str_field(&payload, "channel_id"),
            message_id: str_field(&payload, "message_id"),
            custom_id: str_field(&payload, "custom_id"),
            member,
            expires_at: str_field(&payload, "expires_at"),
            raw: payload,
            client,
        })
    }

    async fn callback(&self, body: Value) -> Result<Value> {
        self.client
            .raw(
                reqwest::Method::POST,
                &format!("/interactions/{}/callback", self.id),
                Some(body),
            )
            .await
    }

    /// 仅确认，让用户按钮停止转圈；之后仍可再 reply / update_message 一次。
    pub async fn ack(&self) -> Result<()> {
        self.callback(json!({ "token": self.token, "type": "ack" }))
            .await?;
        Ok(())
    }

    /// 以 bot 身份在原频道回复；`ephemeral` 为 `None` 时取服务端默认 true（仅点击者可见）。
    /// 返回新消息对象。
    pub async fn reply(
        &self,
        content: &str,
        card: Option<Value>,
        ephemeral: Option<bool>,
    ) -> Result<Value> {
        let mut body = json!({
            "token": self.token,
            "type": "reply",
            "content": content,
        });
        if let Some(card) = card {
            body["card"] = card;
        }
        if let Some(ephemeral) = ephemeral {
            body["ephemeral"] = json!(ephemeral);
        }
        self.callback(body).await
    }

    /// 更新原消息的 card 和/或 content。
    pub async fn update_message(
        &self,
        content: Option<&str>,
        card: Option<Value>,
    ) -> Result<Value> {
        let mut body = json!({ "token": self.token, "type": "update_message" });
        if let Some(content) = content {
            body["content"] = json!(content);
        }
        if let Some(card) = card {
            body["card"] = card;
        }
        self.callback(body).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_payload() -> Value {
        json!({
            "id": "1234567890123456789",
            "token": "owlint_abc",
            "guild_id": "guild-uuid",
            "channel_id": "channel-uuid",
            "message_id": "9876543210",
            "custom_id": "approve:42",
            "member": {"user_id": "user-uuid", "username": "alice", "roles": ["role-a"]},
            "expires_at": "2026-07-26T12:15:00Z"
        })
    }

    #[test]
    fn from_value_parses_fields() {
        let client = Client::new("https://owl.example.com", "owlbot_test").unwrap();
        let interaction = Interaction::from_value(client, sample_payload()).unwrap();
        assert_eq!(interaction.id, "1234567890123456789");
        assert_eq!(interaction.token, "owlint_abc");
        assert_eq!(interaction.custom_id, "approve:42");
        assert_eq!(interaction.message_id, "9876543210");
        assert_eq!(interaction.member.user_id, "user-uuid");
        assert_eq!(interaction.member.roles, vec!["role-a".to_string()]);
        assert_eq!(interaction.expires_at, "2026-07-26T12:15:00Z");
    }

    #[test]
    fn from_value_rejects_missing_token() {
        let client = Client::new("https://owl.example.com", "owlbot_test").unwrap();
        assert!(Interaction::from_value(client, json!({ "id": "1" })).is_err());
    }
}
