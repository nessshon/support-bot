from typing import Dict, List, Optional, Type, Union, cast

from aiogram import Bot
from aiogram.methods import SendMediaGroup
from aiogram.types import (
    Audio,
    Document,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    PhotoSize,
    TelegramObject,
    Video,
)
from aiogram.types.base import UNSET_PROTECT_CONTENT
from pydantic import Field

Media = Union[PhotoSize, Video, Audio, Document]
InputMedia = Union[InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument]

INPUT_TYPES: Dict[str, Type[InputMedia]] = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "audio": InputMediaAudio,
    "document": InputMediaDocument,
}


class Album(TelegramObject):
    """
    Class representing an album of media files.
    """

    photo: Optional[List[PhotoSize]] = None
    video: Optional[List[Video]] = None
    audio: Optional[List[Audio]] = None
    document: Optional[List[Document]] = None
    caption: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)

    @property
    def media_types(self) -> List[str]:
        """
        Get the types of media in album.

        :return: A list of media types.
        """
        return [media_type for media_type in INPUT_TYPES if getattr(self, media_type)]

    @property
    def as_media_group(self) -> List[InputMedia]:
        """
        Convert the album to a list of InputMedia objects for sending as a media group.

        :return: A list of InputMedia objects.
        """
        bot = cast(Bot, self.bot)
        group = [
            INPUT_TYPES[media_type](media=media.file_id, parse_mode=bot.default.parse_mode)
            for media_type in self.media_types
            for media in getattr(self, media_type)
        ]
        if group:
            group[0].caption = self.caption
        return group

    def copy_to(
            self,
            chat_id: Union[int, str],
            message_thread_id: Optional[int] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[bool] = UNSET_PROTECT_CONTENT,
            reply_to_message_id: Optional[int] = None,
            allow_sending_without_reply: Optional[bool] = None,
    ) -> SendMediaGroup:
        """
        Copy the album to a SendMediaGroup object for sending.

        :param chat_id: The ID of the chat to send the media group to.
        :param message_thread_id: The ID of the message thread.
        :param disable_notification: Whether to disable notification for the message.
        :param protect_content: Whether to protect the content of the message.
        :param reply_to_message_id: The ID of the message to reply to.
        :param allow_sending_without_reply: Whether to allow sending without a reply.
        :return: A SendMediaGroup object.
        """
        return SendMediaGroup(
            chat_id=chat_id,
            media=self.as_media_group,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
        ).as_(self._bot)
