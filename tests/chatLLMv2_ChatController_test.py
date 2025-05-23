import unittest
from ChatLLMv2.ChatController import (
    ChatController
)
from ChatLLMv2.ChatModel.Base import (
    BaseModel,
)
from ChatLLMv2.DataHandler import (
    ChatMessage,
    ChatRecord,
    TableBase,
)
from TestBase import TestBase


class ChatController_Test(TestBase):

    def test_get_chat_from_db(self):
        TableBase.metadata.create_all(self.engine)
        chatMessage1 = ChatMessage("user", "hi1")
        chatMessage2 = ChatMessage("ai", "hi2")
        chatMessage3 = ChatMessage("user", "hi3")
        chatMessage4 = ChatMessage("ai", "hi4")
        chatRecord1 = ChatRecord("chat1", [
            chatMessage1,
            chatMessage2,
        ])
        chatRecord2 = ChatRecord("chat2", [
            chatMessage3,
            chatMessage4,
        ])
        self.session.add(chatRecord1)
        self.session.add(chatRecord2)
        self.session.commit()
        model = BaseModel()
        chatController = ChatController(self.session, model, "chat1")
        chatController2 = ChatController(self.session, model, "chat2")
        self.assertEqual(chatController.currentChatRecords.messages[0].text, "hi1")
        self.assertEqual(chatController.currentChatRecords.messages[1].text, "hi2")
        self.assertEqual(chatController2.currentChatRecords.messages[0].text, "hi3")
        self.assertEqual(chatController2.currentChatRecords.messages[1].text, "hi4")

    def test_chatId_set(self):
        TableBase.metadata.create_all(self.engine)
        chatMessage1 = ChatMessage("user", "hi1")
        chatMessage2 = ChatMessage("ai", "hi2")
        chatMessage3 = ChatMessage("user", "hi3")
        chatMessage4 = ChatMessage("ai", "hi4")
        chatRecord1 = ChatRecord("chat1", [
            chatMessage1,
            chatMessage2,
        ])
        chatRecord2 = ChatRecord("chat2", [
            chatMessage3,
            chatMessage4,
        ])
        self.session.add(chatRecord1)
        self.session.add(chatRecord2)
        self.session.commit()
        model = BaseModel()
        chatController = ChatController(self.session, model, "chat1")
        self.assertEqual(chatController.currentChatRecords.messages[0].text, "hi1")
        chatController.chatId = "chat2"
        self.assertEqual(chatController.currentChatRecords.messages[0].text, "hi3")

    def test_llm_invoke(self):
        TableBase.metadata.create_all(self.engine)

        model = BaseModel()
        chatController = ChatController(self.session, model, "test1")
        chatController.invokeLLM(ChatMessage("user", "hello"))
        self.assertEqual(chatController.currentChatRecords.messages[0].text, "hello")
        self.assertEqual(chatController.currentChatRecords.messages[1].text, "MockMessage: hello")

        chatController2 = ChatController(self.session, model, "test1")
        chatController2.invokeLLM(ChatMessage("user", "hello2"))
        chatController2.invokeLLM(ChatMessage("user", "hello3"))
        self.assertEqual(chatController.currentChatRecords.messages[0].text, "hello")
        self.assertEqual(chatController.currentChatRecords.messages[1].text, "MockMessage: hello")
        self.assertEqual(chatController.currentChatRecords.messages[2].text, "hello2")
        self.assertEqual(chatController.currentChatRecords.messages[3].text, "MockMessage: hello2")
        self.assertEqual(chatController.currentChatRecords.messages[4].text, "hello3")
        self.assertEqual(chatController.currentChatRecords.messages[5].text, "MockMessage: hello3")

        retrieved_chat = self.session.query(ChatRecord).where(ChatRecord.chatId == "test1").first()
        self.assertEqual(len(chatController2.currentChatRecords.messages), len(retrieved_chat.messages))  # type: ignore


if __name__ == '__main__':
    unittest.main()
