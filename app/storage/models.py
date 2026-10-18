from dataclasses import dataclass


# Stored as JSON: a new field needs a default that reads old records right, renaming or removing one breaks them
@dataclass
class UserData:
    message_thread_id: int | None
    message_silent_id: int | None
    message_silent_mode: bool

    id: int
    full_name: str
    username: str | None
    created_at: str
    state: str = "member"
    is_banned: bool = False
    language_code: str | None = None
    group_id: int | None = None
    is_verified: bool = True

    @property
    def url(self) -> str:
        if self.username and self.username != "-":
            return f"https://t.me/{self.username[1:]}"
        return f"tg://user?id={self.id}"

    # A topic counts only in the group the bot works with now
    def has_topic(self, group_id: int) -> bool:
        return self.message_thread_id is not None and self.group_id == group_id
