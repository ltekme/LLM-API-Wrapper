import typing as t
from pydantic import BaseModel, Field


class chatLLMDataModel:

    class Request(BaseModel):
        class MessageContext(BaseModel):
            message: str = Field(
                description="The message that get sent to LLM"
            )
            media: t.Optional[list[str]] = Field(
                description="List of attachments along side of user text",
                default=None
            )

        chatId: str = Field(
            description="The chat ID, should be uuid string",
        )
        content: MessageContext = Field(
            description="content to be sent to LLM",
        )
        context: t.Optional[dict[str, str]] = Field(
            description="Context of this request, will be sent to LLM",
            default=None
        )
        disableTTS: t.Optional[bool] = Field(
            description="controls weather to include TTS audio data in the response",
            default=None
        )

    class Response(BaseModel):
        message: str = Field(
            description="LLM Response Message",
        )
        chatId: str = Field(
            description="The Chat id of the chat this message belong to",
        )
        ttsAudio: str = Field(
            description="TTS Audio data in base64",
        )


class geocodeDataModel:

    class Request(BaseModel):
        latitude: float = Field(
            description="latitude of the location to be looked up",
        )
        longitude: float = Field(
            description="longitude of the location to be looked up",
        )

    class Response(BaseModel):
        localtion: str = Field(
            description="location lookup of the given longitude, latitude",
        )
