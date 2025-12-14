import sqlite3
from typing import List, Tuple, Optional


class Database:
    def __init__(self, path: str = "bot.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Пользователи
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
        """)

        # Админы
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
        """)

        # Каналы-спонсоры
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            url TEXT NOT NULL,
            btn_text TEXT NOT NULL
        )
        """)

        # Файлы
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            caption TEXT
        )
        """)

        self.conn.commit()

    # ================= USERS =================
    def add_user(self, user_id: int):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        self.conn.commit()

    def users_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

    # ================= ADMINS =================
    def add_admin(self, user_id: int):
        self.cursor.execute(
            "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
            (user_id,)
        )
        self.conn.commit()

    def remove_admin(self, user_id: int):
        self.cursor.execute(
            "DELETE FROM admins WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()

    def is_admin(self, user_id: int) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM admins WHERE user_id = ?",
            (user_id,)
        )
        return self.cursor.fetchone() is not None

    # ================= CHANNELS =================
    def add_channel(self, chat_id: str, url: str, btn_text: str):
        self.cursor.execute(
            "INSERT INTO channels (chat_id, url, btn_text) VALUES (?, ?, ?)",
            (chat_id, url, btn_text)
        )
        self.conn.commit()

    def del_channel(self, channel_id: int):
        self.cursor.execute(
            "DELETE FROM channels WHERE id = ?",
            (channel_id,)
        )
        self.conn.commit()

    def get_channels(self) -> List[Tuple[int, str, str, str]]:
        self.cursor.execute(
            "SELECT id, chat_id, url, btn_text FROM channels"
        )
        return self.cursor.fetchall()

    # ================= FILES =================
    def add_file(self, file_id: str, caption: str) -> int:
        self.cursor.execute(
            "INSERT INTO files (file_id, caption) VALUES (?, ?)",
            (file_id, caption)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_file(self, file_id: int) -> Optional[Tuple[str, str]]:
        self.cursor.execute(
            "SELECT file_id, caption FROM files WHERE id = ?",
            (file_id,)
        )
        return self.cursor.fetchone()

    def list_files(self) -> List[Tuple[int, str]]:
        self.cursor.execute(
            "SELECT id, caption FROM files"
        )
        return self.cursor.fetchall()
