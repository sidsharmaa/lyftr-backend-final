import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Any
from app.config import settings
from app.models import WebhookPayload, MessageRow

logger = logging.getLogger(__name__)

class SQLiteRepository:
    def __init__(self, db_url: str):
        self.db_path = db_url.replace("sqlite:///", "")
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        q = """
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            from_msisdn TEXT NOT NULL,
            to_msisdn TEXT NOT NULL,
            ts TEXT NOT NULL,
            text TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(ts);
        """
        with self._get_conn() as conn:
            conn.executescript(q)
            conn.commit()

    def insert_message(self, payload: WebhookPayload) -> str:
        now = datetime.now(timezone.utc).isoformat()
        sql = """
        INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_conn() as conn:
                conn.execute(sql, (
                    payload.message_id,
                    payload.sender,
                    payload.recipient,
                    payload.ts.isoformat().replace("+00:00", "Z"),
                    payload.text,
                    now
                ))
                conn.commit()
            return "created"
        except sqlite3.IntegrityError:
            return "duplicate"
        except Exception as e:
            logger.error(f"DB Error: {e}")
            raise e

    def get_messages(self, limit: int, offset: int, 
                     sender: Optional[str] = None, 
                     since: Optional[datetime] = None, 
                     text_search: Optional[str] = None) -> Tuple[List[MessageRow], int]:
        base_query = "FROM messages WHERE 1=1"
        params: List[Any] = []

        if sender:
            base_query += " AND from_msisdn = ?"
            params.append(sender)
        if since:
            base_query += " AND ts >= ?"
            params.append(since.isoformat())
        if text_search:
            base_query += " AND text LIKE ?"
            params.append(f"%{text_search}%")

        count_sql = f"SELECT COUNT(*) {base_query}"
        data_sql = f"SELECT * {base_query} ORDER BY ts ASC, message_id ASC LIMIT ? OFFSET ?"
        
        with self._get_conn() as conn:
            total = conn.execute(count_sql, params).fetchone()[0]
            params.append(limit)
            params.append(offset)
            cursor = conn.execute(data_sql, params)
            rows = cursor.fetchall()

        results = [
            MessageRow(
                message_id=row["message_id"],
                from_msisdn=row["from_msisdn"],
                to_msisdn=row["to_msisdn"],
                ts=datetime.fromisoformat(row["ts"].replace("Z", "+00:00")),
                text=row["text"],
                created_at=datetime.fromisoformat(row["created_at"])
            ) for row in rows
        ]
        
        return results, total

    def get_stats(self) -> dict:
        stats_sql = """
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT from_msisdn) as senders,
            MIN(ts) as first_ts,
            MAX(ts) as last_ts
        FROM messages
        """
        
        senders_sql = """
        SELECT from_msisdn, COUNT(*) as count
        FROM messages
        GROUP BY from_msisdn
        ORDER BY count DESC
        LIMIT 10
        """

        with self._get_conn() as conn:
            overall = conn.execute(stats_sql).fetchone()
            top_senders = conn.execute(senders_sql).fetchall()

        return {
            "total_messages": overall["total"],
            "senders_count": overall["senders"],
            "first_message_ts": overall["first_ts"],
            "last_message_ts": overall["last_ts"],
            "messages_per_sender": [
                {"from": row["from_msisdn"], "count": row["count"]} 
                for row in top_senders
            ]
        }

db_repo = SQLiteRepository(settings.database_url)