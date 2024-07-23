from abc import abstractmethod, ABCMeta

# Add other languages and their corresponding codes as needed.
# You can also keep only one language by removing the line with the unwanted language.
SUPPORTED_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}


class Text(metaclass=ABCMeta):
    """
    Abstract base class for handling text data in different languages.
    """

    def __init__(self, language_code: str) -> None:
        """
        Initializes the Text instance with the specified language code.

        :param language_code: The language code (e.g., "ru" or "en").
        """
        self.language_code = language_code if language_code in SUPPORTED_LANGUAGES.keys() else "en"

    @property
    @abstractmethod
    def data(self) -> dict:
        """
        Abstract property to be implemented by subclasses. Represents the language-specific text data.

        :return: Dictionary containing language-specific text data.
        """
        raise NotImplementedError

    def get(self, code: str) -> str:
        """
        Retrieves the text corresponding to the provided code in the current language.

        :param code: The code associated with the desired text.
        :return: The text in the current language.
        """
        return self.data[self.language_code][code]


class TextMessage(Text):
    """
    Subclass of Text for managing text messages in different languages.
    """

    @property
    def data(self) -> dict:
        """
        Provides language-specific text data for text messages.

        :return: Dictionary containing language-specific text data for text messages.
        """
        return {
            "en": {
                "select_language": "👋 <b>Hello</b>, {full_name}!\n\nSelect language:",
                "change_language": "<b>Select language:</b>",
                "main_menu": "<b>Write your ant blog post</b>, and we will publish it as soon as possible:",
                "message_sent": "<b>Blog post sent!</b> Expect it to be published soon.",
                "message_edited": (
                    "<b>The blog post was edited only in your chat.</b> "
                    "To publish the edited post, send it as a new message."
                ),
                "rules": (
                    "<b>Rules for using the bot are under development.<b>"
                    "For any questions, please contact us via <a href=\"https://t.me/keeperstvo_prosto/1\">chat</a>"
                ),
                "user_started_bot": (
                    "<b>User {name} started the bot!</b>\n\n"
                    "List of available commands:\n"
                    "• /ban - Block/Unblock user"
                    "• /silent - Activate/Deactivate silent mode"
                    "• /information - User information"
                ),
                "user_restarted_bot": "<b>User {name} restarted the bot!</b>",
                "user_stopped_bot": "<b>User {name} stopped the bot!</b>",
                "user_blocked": "<b>User blocked!</b> Blog posts from the user are not accepted.",
                "user_unblocked": "<b>User unblocked!</b> Blog posts from the user are being accepted again.",
                "blocked_by_user": "<b>Post not sent!</b> The bot has been blocked by the user.",
                "user_information": (
                    "<b>ID:</b>\n"
                    "- <code>{id}</code>\n"
                    "<b>Name:</b>\n"
                    "- {full_name}\n"
                    "<b>Username:</b>\n"
                    "- {username}\n"
                ),
                "message_not_sent": "<b>Post not sent!</b> An unexpected error occurred.",
                "message_sent_to_user": "<b>Post sent to user!</b>",
                "silent_mode_enabled": (
                    "<b>Silent mode activated!</b> Notifications will not be delivered to the user."
                ),
                "silent_mode_disabled": (
                    "<b>Silent mode deactivated!</b> The user will receive all notifications."
                ),
            },
            "ru": {
                "select_language": "👋 <b>Привет</b>, {full_name}!\n\nВыберите язык:",
                "change_language": "<b>Выберите язык:</b>",
                "main_menu": "<b>Напишите свой пост о муравьях</b>, и я опубликю его в ближайшее время в Вашей теме проекта @keeperstvo_prosto:",
                "message_sent": "<b>Пост отправлен!</b> В ближайшее время он будет опубликован.",
                "message_edited": (
                    "<b>Пост отредактирован только в вашем чате.</b> "
                    "Чтобы опубликовать отредактированный пост, отправьте его как новое сообщение."
                ),
                "rules": (
                    "<b>Правила использования бота находятся в разработке.<b>"
                    "По всем вопросам обращайтесь в <a href=\"https://t.me/keeperstvo_prosto/1\">чат</a>"
                ),
                "user_started_bot": (
                    "<b>Пользователь {name} запустил(а) бота!</b>\n\n"
                    "Список доступных команд:\n\n"
                    "• /ban - Заблокировать/Разблокировать пользователя"
                    "• /silent - Активировать/Деактивировать тихий режим"
                    "• /information - Информация о пользователе"
                ),
                "user_restarted_bot": "<b>Пользователь {name} перезапустил(а) бота!</b>",
                "user_stopped_bot": "<b>Пользователь {name} остановил(а) бота!</b>",
                "user_blocked": "<b>Пользователь заблокирован!</b> Посты от пользователя не принимаются.",
                "user_unblocked": "<b>Пользователь разблокирован!</b> Посты от пользователя вновь принимаются.",
                "blocked_by_user": "<b>Пост не отправлен!</b> Бот был заблокирован пользователем.",
                "user_information": (
                    "<b>ID:</b>\n"
                    "- <code>{id}</code>\n"
                    "<b>Имя:</b>\n"
                    "- {full_name}\n"
                    "<b>Username:</b>\n"
                    "- {username}\n"
                ),
                "message_not_sent": "<b>Пост не отправлен!</b> Произошла неожиданная ошибка.",
                "message_sent_to_user": "<b>Пост отправлен пользователю!</b>",
                "silent_mode_enabled": (
                    "<b>Тихий режим активирован!</b> Уведомления не будут доставлены пользователю."
                ),
                "silent_mode_disabled": (
                    "<b>Тихий режим деактивирован!</b> Пользователь будет получать все уведомления."
                )
            },
        }
