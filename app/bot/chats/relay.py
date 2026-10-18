from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import (
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    MessageReactionUpdated,
    ReactionTypeCustomEmoji,
    ReactionTypeEmoji,
    ReplyParameters,
)
from aiogram.types.media_union import MediaUnion

from app.storage import UserStorage


# Up to 100 IDs in ascending order; albums stay grouped, what can't be sent is skipped, not failed
async def copy_ids(
    bot: Bot,
    users: UserStorage,
    from_chat_id: int,
    message_ids: list[int],
    chat_id: int,
    thread_id: int | None,
    *,
    forwarded: bool,
) -> None:
    if forwarded:
        sent = await bot.forward_messages(chat_id, from_chat_id, message_ids, message_thread_id=thread_id)
    else:
        sent = await bot.copy_messages(chat_id, from_chat_id, message_ids, message_thread_id=thread_id)
    await users.add_links(from_chat_id, message_ids, chat_id, [m.message_id for m in sent])


# Copies are the bot's own messages, so edits and /delete reach them; forwards keep their source
async def send(bot: Bot, users: UserStorage, messages: list[Message], chat_id: int, thread_id: int | None) -> None:
    first = messages[0]
    message_ids = [m.message_id for m in messages]
    if first.forward_origin:
        await copy_ids(bot, users, first.chat.id, message_ids, chat_id, thread_id, forwarded=True)
        return

    reply = await reply_parameters(first, users, chat_id)
    if len(messages) == 1:
        # copyMessage, not copyMessages: a message that can't be copied fails, and the sender is told
        copied = await bot.copy_message(
            chat_id, first.chat.id, first.message_id, message_thread_id=thread_id, reply_parameters=reply
        )
        await users.add_links(first.chat.id, message_ids, chat_id, [copied.message_id])
        return

    media: list[MediaUnion] = [m for m in map(input_media, messages) if isinstance(m, MediaUnion)]
    if reply is None or len(media) != len(messages):
        await copy_ids(bot, users, first.chat.id, message_ids, chat_id, thread_id, forwarded=False)
        return
    # copyMessages can't reply: an album that is a reply is sent again from the same files
    album = await bot.send_media_group(chat_id, media, message_thread_id=thread_id, reply_parameters=reply)
    await users.add_links(first.chat.id, message_ids, chat_id, [m.message_id for m in album])


async def reply_parameters(message: Message, users: UserStorage, chat_id: int) -> ReplyParameters | None:
    if message.reply_to_message is None:
        return None
    link = await users.get_link(message.chat.id, message.reply_to_message.message_id)
    if link is None or link[0] != chat_id:
        return None
    return ReplyParameters(message_id=link[1], allow_sending_without_reply=True)


def input_media(message: Message) -> MediaUnion | InputMediaAnimation | None:
    # parse_mode=None: the entities go as they are, the bot's default HTML would conflict with them
    caption: dict[str, Any] = {
        "caption": message.caption,
        "caption_entities": message.caption_entities,
        "parse_mode": None,
    }
    visual: dict[str, Any] = {
        **caption,
        "show_caption_above_media": message.show_caption_above_media,
        "has_spoiler": message.has_media_spoiler,
    }
    # An animation message also carries a document, so it is checked first
    if message.animation:
        return InputMediaAnimation(media=message.animation.file_id, **visual)
    if message.photo:
        return InputMediaPhoto(media=message.photo[-1].file_id, **visual)
    if message.video:
        return InputMediaVideo(media=message.video.file_id, **visual)
    if message.audio:
        return InputMediaAudio(media=message.audio.file_id, **caption)
    if message.document:
        return InputMediaDocument(media=message.document.file_id, **caption)
    return None


# False: no pair to edit (older than the link, forwarded, deleted)
async def edit(bot: Bot, users: UserStorage, message: Message) -> bool:
    link = await users.get_link(message.chat.id, message.message_id)
    if link is None:
        return False
    chat_id, message_id = link
    try:
        if message.text is not None:
            # Explicit None: the bot's default would turn the copy's preview off, also via disable_web_page_preview
            await bot.edit_message_text(
                message.text,
                chat_id=chat_id,
                message_id=message_id,
                entities=message.entities,
                parse_mode=None,
                link_preview_options=message.link_preview_options,
                disable_web_page_preview=None,
            )
        elif media := input_media(message):
            await bot.edit_message_media(media, chat_id=chat_id, message_id=message_id)
        else:
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                parse_mode=None,
            )
    except TelegramForbiddenError:
        # The user blocked the bot, or the bot was removed from the group
        return False
    except TelegramBadRequest as ex:
        # An edit of fields the copy does not show
        return "message is not modified" in ex.message
    return True


# Telegram doesn't report deletions, so /delete removes the pair; each side deletes only its own messages
async def delete_pair(bot: Bot, users: UserStorage, command: Message) -> str:
    reply = command.reply_to_message
    if reply is None or reply.from_user is None or reply.from_user.id == bot.id:
        return "message_not_found"
    link = await users.get_link(command.chat.id, reply.message_id)
    if link is None:
        return "message_not_found"
    # deleteMessage: 48 hours; the original is the older one (a queued pair comes later), so both sides or neither
    if datetime.now(UTC) - reply.date >= timedelta(hours=48):
        return "message_not_deleted"
    try:
        await bot.delete_message(*link)
    except TelegramForbiddenError:
        return "message_delete_failed"
    except TelegramBadRequest as ex:
        # The pair was deleted by hand: only this side is left
        if "message to delete not found" not in ex.message:
            return "message_delete_failed"
    try:
        await reply.delete()
    except TelegramBadRequest:
        return "message_delete_failed"
    return "message_deleted"


async def copy_reaction(
    bot: Bot, users: UserStorage, event: MessageReactionUpdated, person_id: int, pair: tuple[int, int]
) -> None:
    # Bots can't use paid reactions; of a few reactions of one person the first one is copied
    reaction = next((r for r in event.new_reaction if r.type != "paid"), None)
    # Bots set one reaction: several admins share it, and removing one shows the latest of the others
    shown = await users.update_reaction(
        event.chat.id, event.message_id, person_id, reaction.model_dump(mode="json") if reaction else None
    )
    pair_reaction: ReactionTypeEmoji | ReactionTypeCustomEmoji | None = None
    if shown is not None and shown["type"] == "custom_emoji":
        pair_reaction = ReactionTypeCustomEmoji(custom_emoji_id=shown["custom_emoji_id"])
    elif shown is not None:
        pair_reaction = ReactionTypeEmoji(emoji=shown["emoji"])
    chat_id, message_id = pair
    # Custom emoji not allowed, the bot blocked, a long flood wait: a reaction is not worth any of them
    with suppress(TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter):
        await bot.set_message_reaction(
            chat_id=chat_id, message_id=message_id, reaction=[pair_reaction] if pair_reaction else []
        )
