import typing as t
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from PIL import Image
from io import BytesIO
import base64


class MessageContentMedia:
    def __init__(self, data: str, mime_type: str) -> None:
        self._data = data
        self._mime_type = mime_type

    @property
    def uri(self) -> str:
        return f"data:{self._mime_type};base64,{self._data}"

    @property
    def as_lcMessageDict(self) -> dict[str, t.Any]:
        return {
            "type": "media",
            "data": self._data,
            "mime_type": self._mime_type,
        }

    @classmethod
    def from_uri(cls, uri: str) -> "MessageContentMedia":
        if not uri.startswith("data"):
            raise ValueError("Must be data url")
        data = uri.split(",")[1]
        mime_type = uri.split(";")[0].split(":")[1]

        # safe image processing
        if mime_type.split("/")[0] == "image" and mime_type.split("/")[0] != "gif":
            target_format = "png"
            processed_image = BytesIO()
            im = Image.open(BytesIO(base64.b64decode(data)))
            im.save(processed_image, target_format)
            data = base64.b64encode(processed_image.getvalue()).decode()
            mime_type = f"image/{target_format}"

        return cls(data, mime_type)


class MessageContent:
    def __init__(self, text: str, media: list[MessageContentMedia] = []) -> None:
        self.text: str = text
        self.media: list[MessageContentMedia] = media

    def as_str(self):
        return f"{self.text};{";".join([str(m.as_lcMessageDict) for m in self.media])}"

    def __repr__(self):
        return self.as_str()


class ChatMessage:
    lcMessageMapping: dict[str, t.Type[AIMessage | SystemMessage | HumanMessage]] = {
        "ai": AIMessage,
        "system": SystemMessage,
        "human": HumanMessage
    }

    def __init__(self, role: t.Literal["ai", "human", "system"], content: MessageContent | str) -> None:
        self.role: t.Literal["ai", "human", "system"] = role
        if isinstance(content, MessageContent):
            self.content: MessageContent = content
        else:
            self.content: MessageContent = MessageContent(str(content))

    @property
    def message_list(self) -> list[dict[str, t.Any]]:
        """Return the human message list in the format of langchain template message"""
        return [{
            "type": "text",
            "text": str(self.content.text)
        }] + [image.as_lcMessageDict for image in self.content.media]

    @property
    def lcMessage(self) -> t.Union[AIMessage, SystemMessage, HumanMessage]:
        return self.lcMessageMapping[self.role](content=self.message_list)  # type: ignore

    def __repr__(self) -> str:
        return f"{self.role};{self.content}"

    def __deepcopy__(self, memo):
        return ChatMessage(self.role, self.content)
