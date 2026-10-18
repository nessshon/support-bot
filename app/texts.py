import tomllib
from pathlib import Path
from string import Formatter

# One file per language, the file name is the language code: copy en.toml to add a language, delete a file to remove it
LOCALES_DIR = Path(__file__).parents[1] / "locales"
# chats/topic.py:user_details
USER_DETAILS = {"name", "full_name", "id", "username", "language", "state", "is_banned", "silent_mode", "created_at"}
# What the code puts into each text; the other texts are sent as they are
PLACEHOLDERS = {
    "select_language": {"full_name"},
    "main_menu": {"full_name"},
    "too_many_messages": {"seconds"},
    "user_started_bot": USER_DETAILS,
    "user_restarted_bot": USER_DETAILS,
    "user_stopped_bot": USER_DETAILS,
    "user_information": USER_DETAILS,
}


def load() -> dict[str, dict[str, str]]:
    texts = {path.stem: tomllib.loads(path.read_text(encoding="utf-8")) for path in sorted(LOCALES_DIR.glob("*.toml"))}
    if not texts:
        raise ValueError(f"No language files in {LOCALES_DIR}")
    # A missing text fails on start, not in the middle of a dialog
    keys = set().union(*texts.values())
    for code, language in texts.items():
        if missing := keys - language.keys():
            raise ValueError(f"{code}.toml has no {', '.join(sorted(missing))}")
        # An edited text with a typo in a placeholder or a stray brace fails on start, not on a user's first message
        for key, text in language.items():
            try:
                fields = {field for _, field, _, _ in Formatter().parse(text) if field is not None}
            except ValueError as ex:
                raise ValueError(f"{code}.toml, {key}: {ex}") from ex
            if unknown := fields - PLACEHOLDERS.get(key, set()):
                raise ValueError(f"{code}.toml, {key}: unsupported {', '.join(sorted('{' + f + '}' for f in unknown))}")
    return texts


TEXTS = load()
SUPPORTED_LANGUAGES = {code: language["language"] for code, language in TEXTS.items()}
# en, or the first language without en.toml: one language is then used for everyone
DEFAULT_LANGUAGE = "en" if "en" in SUPPORTED_LANGUAGES else next(iter(SUPPORTED_LANGUAGES))


class TextMessage:
    def __init__(self, language_code: str | None) -> None:
        self.language_code = language_code if language_code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    def get(self, code: str) -> str:
        return TEXTS[self.language_code][code]
