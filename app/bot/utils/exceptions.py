class CreateForumTopicException(Exception):
    """
    Exception raised when there is an issue creating a forum topic, typically when the chat is not found.
    """
    message = (
        "Unable to create a topic on the forum. The chat was not found, "
        "or forum topics are not activated."
    )

    def __init__(self) -> None:
        super().__init__(self.message)


class NotEnoughRightsException(Exception):
    """
    Exception raised when the bot doesn't have enough rights to perform a specific action.
    """
    message = "The bot doesn't have sufficient rights to create a forum topic."

    def __init__(self) -> None:
        super().__init__(self.message)


# The chat is not configured as a forum or the bot lacks necessary permissions
class NotAForumException(Exception):
    """
    Exception raised when the chat is not a forum.
    """
    message = (
        "The chat is not configured as a forum, or you lack the necessary permissions to manage topics. "
        "Please activate topics first or request administrator privileges."
    )

    def __init__(self) -> None:
        super().__init__(self.message)
