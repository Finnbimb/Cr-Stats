import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.auth import RegisterRequest
from app.core.security import create_access_token
from app.services.clash_royale import fetch_clan_by_tag

router = APIRouter()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # gespeicherter Wert ist kein gültiger bcrypt-Hash (z. B. alter Klartext)
        return False


@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    if len(data.password.strip()) < 3:
        raise HTTPException(status_code=400, detail="Password must be at least 3 characters long")

    if len(data.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")

    blocked_usernames = ["admin", "test", "root"]
    if data.username.lower() in blocked_usernames:
        raise HTTPException(status_code=400, detail="Username is already taken")

    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username is already taken")

    existing_email = db.query(User).filter(User.email == data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email is already registered")

    # Clan über CR-API auflösen, BEVOR wir den User anlegen — schlägt der Lookup
    # fehl, kommt der User gar nicht erst in die DB (kein Stub-Account).
    try:
        clan_data = fetch_clan_by_tag(data.clan_tag)
    except HTTPException as exc:
        if exc.status_code == 404:
            raise HTTPException(status_code=400, detail="Clan-Tag wurde nicht gefunden")
        raise HTTPException(status_code=400, detail="Clan-Tag konnte nicht überprüft werden")

    location = clan_data.get("location") or {}

    new_user = User(
        username=data.username,
        email=data.email,
        password=hash_password(data.password),
        clan_tag=data.clan_tag,
        location_id=location.get("id"),
        location=location.get("name"),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "username": new_user.username,
        "email": new_user.email,
        "clan_tag": new_user.clan_tag,
        "location": new_user.location,
    }


@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

