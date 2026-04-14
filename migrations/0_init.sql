CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS utils;

CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuidv7(),

    github_id BIGINT UNIQUE NOT NULL,
    github_login VARCHAR(128) NOT NULL,
    avatar_url VARCHAR(512),

    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auth.installations (
    id UUID PRIMARY KEY DEFAULT uuidv7(),

    installation_id BIGINT UNIQUE NOT NULL,
    github_account_id BIGINT NOT NULL,
    github_account_login VARCHAR(128) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_installations_account_id ON auth.installations(github_account_id);

CREATE OR REPLACE FUNCTION utils.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_update_users
BEFORE UPDATE ON auth.users
FOR EACH ROW
EXECUTE FUNCTION utils.update_updated_at();

GRANT USAGE ON SCHEMA auth TO "auth-service";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO "auth-service";
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "auth-service";
