from utils.security import hash_password, verify_password
from repositories.users_repo import UserRepository
from repositories.refresh_repo import RefreshTokenRepository
import sqlite3
from utils.jwt_auth import create_access_token, create_refresh_token, verify_token
from datetime import datetime, timedelta

class AuthService:
    def __init__(self):
        self.users = UserRepository()
        self.refresh_repo = RefreshTokenRepository()

    def register(self, username, email, password):
        try:
            self.users.create_user(username, email, hash_password(password))
            return True
        except sqlite3.IntegrityError:
            return False

    def login(self, email, password):
        user = self.users.get_by_email(email)
        if not user:
            return None
        user_id = user["id"]
        username = user["username"]
        password_hash = user["password_hash"]
        if not verify_password(password, password_hash):
            return None
        access = create_access_token({
            "user_id": user_id,
            "username": username
        })
        refresh = create_refresh_token({
            "user_id": user_id,
            "username": username
        })
        expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
        self.refresh_repo.save(user_id, refresh, expires)
        return {
            "access_token": access,
            "refresh_token": refresh
        }

    def refresh(self, token):
        payload = verify_token(token)
        if not payload or payload.get("type") != "refresh":
            return None
        data = self.refresh_repo.get(token)
        if not data:
            return None
        if datetime.utcnow() > datetime.fromisoformat(data["expires_at"]):
            self.refresh_repo.delete(token)
            return None
        user = self.users.get_by_id(data["user_id"])
        return {
            "access_token": create_access_token({
                "user_id": user["id"],
                "username": user["username"]
            })
        }

    def logout(self, token):
        if token:
            self.refresh_repo.delete(token)

    def change_password(self, user_id, old_password, new_password):
        if len(new_password) < 4:
            raise ValueError("Новий пароль має бути не менше 4 символів")

        if len(new_password) > 100:
            raise ValueError("Новий пароль занадто довгий")

        if old_password == new_password:
            raise ValueError("Новий пароль має відрізнятися від старого")

        current_hash = self.users.get_password_hash(user_id)
        if not current_hash:
            raise ValueError("Користувача не знайдено")

        if not verify_password(old_password, current_hash):
            raise ValueError("Старий пароль невірний")

        new_hash = hash_password(new_password)
        self.users.update_password(user_id, new_hash)