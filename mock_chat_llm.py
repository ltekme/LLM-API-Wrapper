import os
import json
import uuid
import typing as t
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import tool

from google.oauth2.service_account import Credentials


class LLMChainModel:
    def __init__(self,
                 credentials: Credentials,
                 model: str,
                 temperature: float,
                 max_tokens: int,
                 ):
        self.llm = ChatVertexAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=None,
            max_retries=2,
            credentials=credentials,
            project=credentials.project_id,
            region="us-central1",
        )

    def invoke(self, messages: list):
        return self.llm.invoke(messages)


class ChatMessage:

    def __init__(self, role: str, content: str, **kwargs) -> None:
        self.role = role
        self.message = content

    def prompt_message(self):
        roles = {
            "user": HumanMessage,
            "ai": AIMessage,
            "system": SystemMessage,
        }
        message = roles.get(self.role, None)
        if not message:
            raise ValueError(f"role must be one of {roles.keys()}")
        return message(self.message)

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.message,
        }


class ChatMessages:

    _chat_messages: t.List[ChatMessage] = []

    def __init__(self, system_message_string: str | None = None) -> None:
        if system_message_string:
            self._chat_messages.append(
                ChatMessage('system', system_message_string))

    def get_all_as_dict(self) -> list:
        return [chatMessage.to_dict() for chatMessage in self._chat_messages]

    def append(self, chatMessage: ChatMessage) -> None:
        if chatMessage.role not in ['user', 'ai']:
            raise ValueError("role must be one of ['user', 'ai']")
        self._chat_messages.append(chatMessage)

    def save_to_file(self, file_path: str) -> None:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w') as f:
            json.dump([chatMessage.to_dict()
                      for chatMessage in self._chat_messages], f, indent=4)

    def get_from_file(self, file_path: str) -> list:
        system_message = None
        if len(self._chat_messages) > 0 and self._chat_messages[0].role == 'system':
            system_message = self._chat_messages[0]
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self._chat_messages = []
            if system_message:
                self._chat_messages.append(system_message)
            return self._chat_messages
        try:
            with open(file_path, 'r') as f:
                data_in_file = json.load(f)
            self._chat_messages = [ChatMessage(**msg) for msg in data_in_file]
            if len(self._chat_messages) > 0 and system_message:
                if self._chat_messages[0].role != 'system':
                    self._chat_messages.insert(0, system_message)
                if self._chat_messages[0].role == 'system' and self._chat_messages[0].message != system_message.message:
                    self._chat_messages[0].message = system_message.message
            return self._chat_messages
        except json.JSONDecodeError:
            self._chat_messages = []
            if system_message:
                self._chat_messages.append(system_message)
            return self._chat_messages

    def add_system_prompt(self, message: str) -> ChatMessage:
        if len(self._chat_messages) > 0 and self._chat_messages[0].role == 'system':
            self._chat_messages[0].message = message
            return self._chat_messages[0]
        system_message = ChatMessage('system', message)
        self._chat_messages.insert(0, system_message)
        return system_message


class ChatLLM:

    chatRecords = ChatMessages(
        system_message_string="""You are a very powerful AI. 
        Context maybe given to assist the assistant in providing better responses.
        Answer the questions to the best of your ability.
        If you don't know the answer, just say you don't know."""
    )
    chatRecordFolderPath = './chat_data'
    store_chat_records = True
    _chatId = str(uuid.uuid4())

    def __init__(self,
                 credentials: Credentials,
                 model: str = "gemini-1.5-pro",
                 temperature: float = 0.9,
                 max_tokens: int = 4096,
                 chatRecordFolderPath: str = './chat_data',
                 chatId: str = None,
                 store_chat_records: bool = True):
        self.llm = LLMChainModel(
            credentials=credentials,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self._chatId = chatId or self._chatId
        self.chatRecordFolderPath = chatRecordFolderPath
        self.store_chat_records = store_chat_records
        if store_chat_records and not os.path.exists(self.chatRecordFolderPath):
            os.makedirs(self.chatRecordFolderPath)
        if store_chat_records:
            self.chatRecords.get_from_file(self.chatRecordFilePath)

    @property
    def chatId(self) -> str:
        return self._chatId

    @chatId.setter
    def chatId(self, value: str) -> None:
        self._chatId = value
        if self.store_chat_records:
            self.chatRecords.get_from_file(self.chatRecordFilePath)

    @property
    def chatRecordFilePath(self) -> str:
        return self.chatRecordFolderPath + "/" + self._chatId + ".json"

    def new_message(self, message: str) -> ChatMessage:
        if not message:
            return ChatMessage('', "Please provide a message.")
        self.chatRecords.append(ChatMessage('user', message))

        # print(self.chatRecords.get_all_as_dict())

        resault = self.llm.invoke(self.chatRecords.get_all_as_dict())

        self.chatRecords.append(ChatMessage('ai', resault.content))

        if self.store_chat_records:
            self.chatRecords.save_to_file(self.chatRecordFilePath)
        return ChatMessage('ai', resault.content)


if __name__ == "__main__":
    credentialsFiles = list(filter(lambda f: f.startswith(
        'gcp_cred') and f.endswith('.json'), os.listdir('.')))
    credentials = Credentials.from_service_account_file(
        credentialsFiles[0])
    chatLLM = ChatLLM(credentials)
    chatLLM.chatId = "0779b6cf-0d3a-4ab1-aaeb-86ff51e09f04"
    while True:
        msg = input("Human: ")
        if msg == "exit":
            break
        print(f"AI({chatLLM.chatId}): " + chatLLM.new_message(msg).message)
