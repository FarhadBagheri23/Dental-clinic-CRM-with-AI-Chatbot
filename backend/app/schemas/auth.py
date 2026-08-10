import re

from pydantic import BaseModel, Field, field_validator

# Credentials are English-only. The UI is RTL Persian, so a user with the
# Persian keyboard layout active types "ادمین" or the Persian digits ۰-۹
# without noticing — those are different codepoints from 0-9 and would fail
# to match the stored password with no clue as to why. Rejecting here gives
# a message that names the real problem instead of "wrong password".
USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
PASSWORD_RE = re.compile(r"^[\x21-\x7E]+$")  # printable ASCII, no spaces

KEYBOARD_HINT = "صفحه‌کلید را روی انگلیسی بگذارید."


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=1, max_length=64,
        description="Latin letters, digits, dot, underscore or hyphen only.",
    )
    password: str = Field(
        min_length=1, max_length=256,
        description="Printable ASCII only, no spaces.",
    )

    @field_validator("username")
    @classmethod
    def username_is_english(cls, v: str) -> str:
        if not USERNAME_RE.fullmatch(v):
            # Punctuation is spelled out in words: bare "." "_" "-" inside
            # Persian text get reordered by the bidi algorithm and render
            # scrambled in the browser.
            raise ValueError(
                "نام کاربری فقط می‌تواند شامل حروف انگلیسی، ارقام، نقطه، زیرخط "
                f"و خط تیره باشد. {KEYBOARD_HINT}"
            )
        return v

    @field_validator("password")
    @classmethod
    def password_is_english(cls, v: str) -> str:
        if not PASSWORD_RE.fullmatch(v):
            raise ValueError(
                f"رمز عبور فقط می‌تواند شامل حروف و نمادهای انگلیسی و بدون فاصله باشد. {KEYBOARD_HINT}"
            )
        return v


class UserOut(BaseModel):
    username: str
    name: str
    role: str
