from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    clan_tag: str

    @field_validator("clan_tag")
    @classmethod
    def normalize_clan_tag(cls, value: str) -> str:
        v = (value or "").strip().upper()
        if not v:
            raise ValueError("Clan-Tag darf nicht leer sein")
        if not v.startswith("#"):
            v = f"#{v}"
        # CR-Tags sind 4–14 Zeichen nach dem #, nur A–Z und 0–9 (0/O wird normalisiert,
        # aber das überlassen wir der CR-API beim Lookup).
        if len(v) < 4 or len(v) > 15:
            raise ValueError("Ungültiger Clan-Tag")
        return v
