import secrets

from captcha.image import ImageCaptcha

ALPHABET = "3469ACDEFGHJKMNPQRTUVWXY"
LENGTH = 5
TTL = 120


def generate() -> tuple[str, bytes]:
    solution = "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))
    # The default 160x60 makes the characters overlap
    return solution, ImageCaptcha(width=280, height=100, font_sizes=(66, 74, 82)).generate(solution).getvalue()


def is_correct(answer: str | None, solution: str) -> bool:
    # compare_digest raises on non-ASCII strings, a Cyrillic answer must be just wrong
    return answer is not None and secrets.compare_digest(answer.replace(" ", "").upper().encode(), solution.encode())
