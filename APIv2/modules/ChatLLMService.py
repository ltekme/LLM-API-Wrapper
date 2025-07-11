import typing as t

import sqlalchemy.orm as so

from google.oauth2.service_account import Credentials

from .Services.User.User import UserChatRecordService

from .ApplicationModel import User

from .ServiceConfig import checksEnabled

from .Services.PermissionAndQuota.Quota import QuotaService
from .Services.PermissionAndQuota.Permission import PermissionService
from .Services.PermissionAndQuota.ServiceBase import permissionRequired
from .Services.PermissionAndQuota.ServiceBase import quotaRequired
from .Services.PermissionAndQuota.ServiceBase import ServiceWithAAA

from .Services.ServiceDefination import CHATLLM_SERIVCE_NAME
from .Services.ServiceDefination import CHATLLM_INVOKE as INVOKE
from .Services.ServiceDefination import CHATLLM_CREATE as CREATE
from .Services.ServiceDefination import CHATLLM_RECALL as RECALL

from ChatLLMv2.ChatModel.Property import AdditionalModelProperty
from ChatLLMv2.ChatModel.Property import InvokeContextValues
from ChatLLMv2.DataHandler import ChatMessage
from ChatLLMv2.ChatController import ChatController
from ChatLLMv2.ChatModel.v1ChainMigrate import v1LLMChainModel

from .exception import NotAuthorizedError
from .exception import ChatLLMServiceError


class ChatLLMService(ServiceWithAAA):
    def __init__(self,
                 user: User,
                 dbSession: so.Session,
                 quotaService: QuotaService,
                 permissionService: PermissionService,
                 userChatRecordService: UserChatRecordService,
                 credentials: t.Optional[Credentials],
                 llmModelProperty: AdditionalModelProperty,
                 ) -> None:
        super().__init__(dbSession, CHATLLM_SERIVCE_NAME, quotaService, permissionService, user)
        self.user = user
        self.userChatRecordService = userChatRecordService
        self.llmModel = v1LLMChainModel(credentials, llmModelProperty)

    def checkUserChatIdAssociation(self, chatId: str) -> bool:
        """
        Check if the user is associated with the chatId.

        :return: True if the user is associated with the chatId, False otherwise.
        """
        self.loggerDebug(f"Checking if user {self.user.id} is associated with chatId {chatId}")
        record = self.userChatRecordService.getByChatId(chatId)
        if record is None:
            return False
        return record.user.id == self.user.id

    @permissionRequired(INVOKE)
    @quotaRequired(INVOKE)
    @checksEnabled(INVOKE)
    def invokeChatModel(self, chatId: str, message: ChatMessage, contextValues: InvokeContextValues,
                        bypassChatAssociationCheck: bool = False,
                        bypassPermssionCheck: bool = False,  # for decorator
                        bypassQuotaCheck: bool = False,  # for decorator
                        bypassServiceEnable: bool = False,  # for decorator
                        ) -> ChatMessage:
        """
        Invoke the chat service with a user and a message.

        :param message: The message to send in the chat.
        :param contextValues: Additional context values for the chat invocation.
        :param bypassPermssionCheck: Whether to bypass the permission check.
        :param bypassChatAssociationCheck: Whether to bypass the chat ID association check.
        :return: The response from the chat service.
        """
        if not self.checkUserChatIdAssociation(chatId) and not bypassChatAssociationCheck:
            raise NotAuthorizedError("The user is not associated with the specified chatId.", INVOKE)

        self.loggerInfo(f"Invoking chat model for user {self.user.id} with chatId {chatId}")
        try:
            return ChatController(
                dbSession=self.dbSession,
                llmModel=self.llmModel,
                chatId=chatId,
            ).invokeLLM(message, contextValues)
        except Exception as e:
            self.loggerError(f"Error invoking chat model for user {self.user.id} with chatId {chatId}: {e}")
            raise ChatLLMServiceError("Failed to invoke chat model.")

    @permissionRequired(CREATE)
    @quotaRequired(CREATE)
    @checksEnabled(CREATE)
    def createChat(self, chatId: t.Optional[str] = None,
                   bypassPermissionCheck: bool = False,  # for decorator
                   bypassQuotaCheck: bool = False,  # for decorator
                   bypassServiceEnable: bool = False,  # for decorator
                   ) -> str:
        """
        Create a new chat session for the user and associate it with the user profile.

        :param chatId: The ID of the chat session to create.
        :param bypassPermissionCheck: Whether to bypass the permission check.
        :return: The ID of the created chat session.
        """
        self.loggerInfo(f"Creating chat session for user {self.user.id} with chatId: {chatId}")
        chatId = chatId if chatId else ChatController(
            dbSession=self.dbSession,
            llmModel=self.llmModel,
            chatId=None,
        ).chatId
        self.loggerInfo(f"Creating chat session with chatId: {chatId} for user {self.user.id}")
        self.userChatRecordService.associateChatIdWithUser(chatId, self.user)
        self.loggerInfo(f"Chat session with chatId: {chatId} created and associated with user {self.user.id}")
        return chatId

    @permissionRequired(RECALL)
    @quotaRequired(RECALL)
    @checksEnabled(RECALL)
    def recall(self, chatId: str,
               bypassChatAssociationCheck: bool = False,
               bypassPermissionCheck: bool = False,  # for decorator
               bypassQuotaCheck: bool = False,  # for decorator
               bypassServiceEnable: bool = False,  # for decorator
               ) -> t.List[ChatMessage]:
        """
        Recall the chat session and return the messages.

        :param bypassPermissionCheck: Whether to bypass the permission check.
        :return: A list of messages in the chat session.
        """
        if not self.checkUserChatIdAssociation(chatId) and not bypassChatAssociationCheck:
            raise NotAuthorizedError("The user is not associated with the specified chatId.", RECALL)

        self.loggerInfo(f"Recalling chat session with chatId: {chatId} for user {self.user.id}")
        return ChatController(
            dbSession=self.dbSession,
            llmModel=self.llmModel,
            chatId=chatId,
        ).currentChatRecords.messages
