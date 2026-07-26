package owlbot

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

const sampleInteraction = `{
	"id": "1234567890123456789",
	"token": "owlint_abc",
	"guild_id": "guild-uuid",
	"channel_id": "channel-uuid",
	"message_id": "9876543210",
	"custom_id": "approve:42",
	"member": {"user_id": "user-uuid", "username": "alice", "roles": ["role-a"]},
	"expires_at": "2026-07-26T12:15:00Z"
}`

func TestParseInteraction(t *testing.T) {
	c := New("https://owl.example.com", "owlbot_test")
	interaction, err := c.ParseInteraction(json.RawMessage(sampleInteraction))
	if err != nil {
		t.Fatalf("ParseInteraction: %v", err)
	}
	if interaction.ID != "1234567890123456789" ||
		interaction.Token != "owlint_abc" ||
		interaction.CustomID != "approve:42" ||
		interaction.MessageID != "9876543210" ||
		interaction.Member.UserID != "user-uuid" ||
		len(interaction.Member.Roles) != 1 {
		t.Fatalf("字段解析不符: %+v", interaction)
	}
	if interaction.ExpiresAt.IsZero() {
		t.Fatal("expires_at 未解析")
	}
	if interaction.client == nil {
		t.Fatal("client 未绑定")
	}
}

func TestSendMessageOptionsVisibleToUserIDs(t *testing.T) {
	raw, err := json.Marshal(SendMessageOptions{
		Content:          "仅你可见",
		VisibleToUserIDs: []string{"user-uuid"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(raw), `"visible_to_user_ids":["user-uuid"]`) {
		t.Fatalf("缺少 visible_to_user_ids: %s", raw)
	}
	// 未设置时必须省略，兼容旧服务端
	raw, _ = json.Marshal(SendMessageOptions{Content: "hi"})
	if strings.Contains(string(raw), "visible_to_user_ids") {
		t.Fatalf("空名单不应序列化: %s", raw)
	}
}

func TestInteractionCallbackRequests(t *testing.T) {
	type captured struct {
		path string
		body map[string]any
	}
	var last captured
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		var body map[string]any
		_ = json.Unmarshal(raw, &body)
		last = captured{path: r.URL.Path, body: body}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":"new-message-id"}`))
	}))
	defer server.Close()

	c := New(server.URL, "owlbot_test")
	interaction, err := c.ParseInteraction(json.RawMessage(sampleInteraction))
	if err != nil {
		t.Fatal(err)
	}

	if err := interaction.Ack(); err != nil {
		t.Fatalf("Ack: %v", err)
	}
	if last.path != "/bot-api/v1/interactions/1234567890123456789/callback" {
		t.Fatalf("回调路径不符: %s", last.path)
	}
	if last.body["type"] != "ack" || last.body["token"] != "owlint_abc" {
		t.Fatalf("ack 请求体不符: %+v", last.body)
	}
	if _, has := last.body["ephemeral"]; has {
		t.Fatal("ack 不应带 ephemeral")
	}

	msg, err := interaction.ReplyText("已处理")
	if err != nil {
		t.Fatalf("ReplyText: %v", err)
	}
	if msg.ID != "new-message-id" {
		t.Fatalf("reply 未返回新消息: %+v", msg)
	}
	if last.body["type"] != "reply" || last.body["content"] != "已处理" {
		t.Fatalf("reply 请求体不符: %+v", last.body)
	}

	ephemeral := false
	if _, err := interaction.Reply("公开回复", InteractionReplyOptions{Ephemeral: &ephemeral}); err != nil {
		t.Fatal(err)
	}
	if last.body["ephemeral"] != false {
		t.Fatalf("ephemeral=false 未序列化: %+v", last.body)
	}

	if err := interaction.UpdateMessage("", map[string]any{"title": "已通过"}); err != nil {
		t.Fatalf("UpdateMessage: %v", err)
	}
	if last.body["type"] != "update_message" {
		t.Fatalf("update_message 请求体不符: %+v", last.body)
	}
	if _, has := last.body["content"]; has {
		t.Fatal("空 content 不应序列化")
	}
}

func TestSendEphemeralBody(t *testing.T) {
	var body map[string]any
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &body)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":"m1"}`))
	}))
	defer server.Close()

	c := New(server.URL, "owlbot_test")
	if _, err := c.SendEphemeral("channel-uuid", "user-uuid", "仅你可见", nil); err != nil {
		t.Fatal(err)
	}
	ids, ok := body["visible_to_user_ids"].([]any)
	if !ok || len(ids) != 1 || ids[0] != "user-uuid" {
		t.Fatalf("visible_to_user_ids 不符: %+v", body)
	}
}
