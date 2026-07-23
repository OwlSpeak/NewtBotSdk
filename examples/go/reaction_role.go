// 反应角色最小示例。
//
//	cd examples/go && go run .  （需设置环境变量）
package main

import (
	"encoding/json"
	"log"
	"os"

	owlbot "github.com/OwlSpeak/OwlBotSdk/go"
)

func main() {
	bot := owlbot.New(os.Getenv("OWL_BASE_URL"), os.Getenv("OWL_BOT_TOKEN"))
	rulesMessageID := os.Getenv("RULES_MESSAGE_ID")
	verifiedRoleID := os.Getenv("VERIFIED_ROLE_ID")

	gw := bot.ConnectGateway()
	gw.On("READY", func(payload json.RawMessage) {
		log.Printf("已连接: %s", string(payload))
	})
	gw.On("MESSAGE_REACTION_ADD", func(payload json.RawMessage) {
		var ev struct {
			MessageID string `json:"message_id"`
			GuildID   string `json:"guild_id"`
			UserID    string `json:"user_id"`
			Emoji     string `json:"emoji"`
		}
		if err := json.Unmarshal(payload, &ev); err != nil {
			return
		}
		if ev.MessageID != rulesMessageID || ev.Emoji != "✅" {
			return
		}
		if _, err := bot.AddMemberRole(ev.GuildID, ev.UserID, verifiedRoleID); err != nil {
			log.Printf("赋角失败: %v", err)
			return
		}
		log.Printf("已赋角 %s", ev.UserID)
	})

	select {}
}
