from dataclasses import dataclass

import httpx


@dataclass
class GitHubUser:
    id: int
    login: str
    avatar_url: str | None


class GitHubOAuthClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    async def exchange_code(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

            if "error" in data:
                raise ValueError(f"GitHub OAuth error: {data['error_description']}")

            return data["access_token"]

    async def get_user_info(self, access_token: str) -> GitHubUser:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            return GitHubUser(
                id=data["id"],
                login=data["login"],
                avatar_url=data.get("avatar_url"),
            )
