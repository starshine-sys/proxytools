from datetime import datetime
from typing import Union, Optional, List

import asyncpg
import hikari

from .enums import *


class ProxyTag:
    """A proxy tag object."""

    prefix: Optional[str]
    suffix: Optional[str]

    def __init__(self, **kwargs):
        self.prefix = kwargs.get("prefix", None)
        self.suffix = kwargs.get("suffix", None)

    def match(self, content: str, keep_proxy: bool = False) -> (bool, Optional[str]):
        """Matches this proxy tag with the given message content.
        Returns a bool and an optional string, string being the content without the proxy tags."""

        if self.prefix is not None and self.suffix is not None:
            if content.startswith(self.prefix) and content.endswith(self.suffix):
                if keep_proxy:
                    return True, content
                return (
                    True,
                    content.removeprefix(self.prefix).removesuffix(self.suffix).strip(),
                )
        elif self.prefix is not None and self.suffix is None:
            if content.startswith(self.prefix):
                if keep_proxy:
                    return True, content
                return True, content.removeprefix(self.prefix).strip()
        elif self.prefix is None and self.suffix is not None:
            if content.endswith(self.suffix):
                if keep_proxy:
                    return True, content
                return True, content.removesuffix(self.suffix).strip()
        return False, None

    def __str__(self):
        return f"{self.prefix or 'None'}text{self.suffix or 'None'}"

    def __repr__(self):
        return f"ProxyTag({self.prefix or 'None'}, {self.suffix or 'None'})"


class Member:
    """A member object from the database."""

    id: int
    hid: str
    system_hid: Optional[str]  # Only optional because not every view returns this
    name: str
    display_name: Optional[str]
    colour: Optional[str]
    description: Optional[str]
    proxy_tags: List[ProxyTag]
    avatar_url: Optional[str]
    created: datetime

    keep_proxy: bool
    description_privacy: Privacy

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.hid = kwargs.get("hid")
        self.system_hid = kwargs.get("system_hid", None)
        self.name = kwargs.get("name")
        self.display_name = kwargs.get("display_name", None)
        self.colour = kwargs.get("colour", None)
        self.avatar_url = kwargs.get("avatar_url", None)
        self.created = kwargs.get("created")
        self.keep_proxy = kwargs.get("keep_proxy")

        proxy_tags: List[dict] = kwargs.get("proxy_tags", [])
        self.proxy_tags = [ProxyTag(**row) for row in proxy_tags]

        self.description_privacy = Privacy.get(kwargs.get("description_privacy"))

    def match_proxy(self, content: str) -> (bool, Optional[str]):
        """Matches all of this member's proxies, and returns the first one that matches.
        Returns False, None if none of the proxies matched."""

        for proxy in self.proxy_tags:
            matched, s = proxy.match(content, keep_proxy=self.keep_proxy)
            if matched:
                return matched, s

        return False, None

    @staticmethod
    async def fetch(
        conn: asyncpg.Connection, id: str, user_id: Optional[hikari.Snowflake] = None
    ) -> Optional["Member"]:
        """Fetches a member by name, ID, or display name (for own members),
        or by ID (for other members)"""

        if user_id is not None:
            return await Member._fetch_own(conn, user_id, id)
        return await Member._fetch(conn, id)

    @staticmethod
    async def _fetch_own(
        conn: asyncpg.Connection, user_id: hikari.Snowflake, id: str
    ) -> Optional["Member"]:
        pass

    @staticmethod
    async def _fetch(conn: asyncpg.Connection, id: str) -> Optional["Member"]:
        pass
