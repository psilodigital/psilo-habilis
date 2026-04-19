"""
Connector credential store.

Manages encrypted OAuth/API credentials for external connectors
(e.g. Gmail, Slack) per company. Credentials are encrypted at rest
using Fernet symmetric encryption.
"""

import json
from typing import Any, Dict, List, Optional

from ..logging import logger

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None  # type: ignore[assignment,misc]
    InvalidToken = Exception  # type: ignore[assignment,misc]


class ConnectorStore:
    """Encrypted credential CRUD backed by Postgres."""

    def __init__(self, database_url: str, encryption_key: str):
        if asyncpg is None:
            raise RuntimeError("asyncpg is required for ConnectorStore")
        if Fernet is None:
            raise RuntimeError("cryptography is required for ConnectorStore")
        if not encryption_key:
            raise RuntimeError(
                "CONNECTOR_ENCRYPTION_KEY is required for ConnectorStore. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        self._database_url = database_url
        self._fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        self._pool: Optional[Any] = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            self._database_url, min_size=1, max_size=5
        )
        logger.info("ConnectorStore connected to database")

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    def _encrypt(self, data: dict) -> bytes:
        """Encrypt a dict as JSON bytes."""
        plaintext = json.dumps(data).encode("utf-8")
        return self._fernet.encrypt(plaintext)

    def _decrypt(self, ciphertext: bytes) -> dict:
        """Decrypt bytes back to a dict."""
        plaintext = self._fernet.decrypt(ciphertext)
        return json.loads(plaintext.decode("utf-8"))

    async def store_credentials(
        self,
        *,
        company_id: str,
        connector_id: str,
        scopes: List[str],
        credentials: Dict[str, Any],
    ) -> None:
        """Store or update connector credentials (encrypted)."""
        if not self._pool:
            raise RuntimeError("ConnectorStore not connected")

        encrypted = self._encrypt(credentials)

        await self._pool.execute(
            """
            INSERT INTO connector_credentials
                (company_id, connector_id, scopes, credentials_enc, status, updated_at)
            VALUES ($1, $2, $3, $4, 'active', now())
            ON CONFLICT ON CONSTRAINT uq_company_connector
            DO UPDATE SET
                scopes = EXCLUDED.scopes,
                credentials_enc = EXCLUDED.credentials_enc,
                status = 'active',
                updated_at = now()
            """,
            company_id,
            connector_id,
            scopes,
            encrypted,
        )
        logger.info(
            "Stored credentials for company=%s connector=%s scopes=%s",
            company_id,
            connector_id,
            scopes,
        )

    async def get_credentials(
        self, company_id: str, connector_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get decrypted credentials. Returns None if not found or revoked."""
        if not self._pool:
            return None

        row = await self._pool.fetchrow(
            """
            SELECT credentials_enc, scopes, status
            FROM connector_credentials
            WHERE company_id = $1 AND connector_id = $2 AND status = 'active'
            """,
            company_id,
            connector_id,
        )
        if not row:
            return None

        try:
            creds = self._decrypt(row["credentials_enc"])
            return {
                "credentials": creds,
                "scopes": row["scopes"],
                "status": row["status"],
            }
        except InvalidToken:
            logger.error(
                "Failed to decrypt credentials for company=%s connector=%s",
                company_id,
                connector_id,
            )
            return None

    async def list_connectors(
        self, company_id: str
    ) -> List[Dict[str, Any]]:
        """List active connectors for a company (without credentials)."""
        if not self._pool:
            return []

        rows = await self._pool.fetch(
            """
            SELECT connector_id, scopes, status, created_at, updated_at
            FROM connector_credentials
            WHERE company_id = $1
            ORDER BY connector_id
            """,
            company_id,
        )
        return [
            {
                "connectorId": r["connector_id"],
                "scopes": r["scopes"],
                "status": r["status"],
                "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
                "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        ]

    async def revoke_credentials(
        self, company_id: str, connector_id: str
    ) -> bool:
        """Revoke credentials. Returns True if a row was updated."""
        if not self._pool:
            return False

        result = await self._pool.execute(
            """
            UPDATE connector_credentials
            SET status = 'revoked', updated_at = now()
            WHERE company_id = $1 AND connector_id = $2 AND status = 'active'
            """,
            company_id,
            connector_id,
        )
        revoked = result == "UPDATE 1"
        if revoked:
            logger.info(
                "Revoked credentials for company=%s connector=%s",
                company_id,
                connector_id,
            )
        return revoked
