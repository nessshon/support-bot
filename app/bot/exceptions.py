class TopicException(Exception):
    message = "Unable to create a topic on the forum."

    def __init__(self) -> None:
        super().__init__(self.message)


class CreateForumTopicException(TopicException):
    message = "Unable to create a topic on the forum. The chat was not found, or forum topics are not activated."


class NotEnoughRightsException(TopicException):
    message = "The bot doesn't have sufficient rights to create a forum topic."


class NotAForumException(TopicException):
    message = (
        "The chat is not configured as a forum, or you lack the necessary permissions to manage topics. "
        "Please activate topics first or request administrator privileges."
    )
