"""Initial auth schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-02
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute("CREATE SCHEMA IF NOT EXISTS utils")

    op.execute(
        """
        CREATE TABLE auth.users (
            id UUID PRIMARY KEY DEFAULT uuidv7(),
            github_id BIGINT UNIQUE NOT NULL,
            github_login VARCHAR(128) NOT NULL,
            avatar_url VARCHAR(512),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE auth.installations (
            id UUID PRIMARY KEY DEFAULT uuidv7(),
            installation_id BIGINT UNIQUE NOT NULL,
            github_account_id BIGINT NOT NULL,
            github_account_login VARCHAR(128) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_installations_account_id ON auth.installations(github_account_id)")

    op.execute(
        """
        CREATE TABLE auth.installation_users (
            installation_id UUID NOT NULL REFERENCES auth.installations(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (installation_id, user_id)
        )
        """
    )
    op.execute("CREATE INDEX idx_installation_users_user_id ON auth.installation_users(user_id)")
    op.execute("CREATE INDEX idx_installation_users_installation_id ON auth.installation_users(installation_id)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION utils.update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_update_users
        BEFORE UPDATE ON auth.users
        FOR EACH ROW
        EXECUTE FUNCTION utils.update_updated_at()
        """
    )

    op.execute('GRANT USAGE ON SCHEMA auth TO "auth-service"')
    op.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO "auth-service"')
    op.execute(
        'ALTER DEFAULT PRIVILEGES IN SCHEMA auth '
        'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "auth-service"'
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_update_users ON auth.users")
    op.execute("DROP TABLE IF EXISTS auth.installation_users")
    op.execute("DROP TABLE IF EXISTS auth.installations")
    op.execute("DROP TABLE IF EXISTS auth.users")
    op.execute("DROP FUNCTION IF EXISTS utils.update_updated_at()")
    op.execute("DROP SCHEMA IF EXISTS auth")
    op.execute("DROP SCHEMA IF EXISTS utils")
