from typing import Optional, List
import datetime

import asyncpg
import hikari

from .enums import *
from .bot import Context


class System:
    """A system object from the database."""

    id: int
    hid: str
    name: Optional[str]
    description: Optional[str]
    tag: Optional[str]
    avatar_url: Optional[str]
    created: datetime.datetime

    description_privacy: Privacy
    list_privacy: Privacy

    # Additional info that may not be present
    accounts: Optional[List[hikari.Snowflake]]
    member_count: Optional[int]

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.hid = kwargs.get("hid")
        self.name = kwargs.get("name", None)
        self.description = kwargs.get("description", None)
        self.tag = kwargs.get("tag", None)
        self.avatar_url = kwargs.get("avatar_url", None)
        self.created = kwargs.get("created")

        self.description_privacy = Privacy.get(kwargs.get("description_privacy"))
        self.list_privacy = Privacy.get(kwargs.get("list_privacy"))

        self.accounts = kwargs.get("accounts", [])
        self.member_count = kwargs.get("member_count", None)

    @property
    def public_description(self) -> Optional[str]:
        """Description if the system's description is public, None otherwise."""

        if self.description_privacy is Privacy.PUBLIC:
            return self.description
        return None

    async def embed(self, ctx: Context) -> hikari.Embed:
        """Returns a embed containing system information."""

        embed = hikari.Embed()
        if self.name is not None:
            embed.title = self.name

        if self.tag is not None:
            embed.add_field("Tag", self.tag, inline=True)

        if len(self.accounts) > 0:
            accounts: List[hikari.User] = []
            for id in self.accounts:
                account = ctx.bot.cache.get_user(id)
                if account is None:
                    account = await ctx.bot.rest.fetch_user(id)
                accounts.append(account)

            embed.add_field(
                f"Linked account{'s' if len(accounts) > 0 else ''}",
                "\n".join(
                    [f"{u.username}#{u.discriminator} ({u.mention})" for u in accounts]
                ),
                inline=False,
            )

        if self.member_count is not None:
            if ctx.author.id in self.accounts:
                val = f"{self.member_count}"
                val += (
                    f" (see `{ctx.prefix}system list`)"
                    if self.member_count != 0
                    else f" (create one with `{ctx.prefix}member new`)"
                )
                embed.add_field("Member count", val, inline=False)
            else:
                if self.list_privacy is Privacy.PUBLIC:
                    embed.add_field(
                        "Member count",
                        f"{self.member_count} (see `{ctx.prefix}system list {self.hid}`)",
                        inline=False,
                    )

        desc = (
            self.description
            if ctx.author.id in self.accounts
            else self.public_description
        )
        if desc is not None:
            embed.add_field("Description", desc, inline=False)

        embed.set_footer(
            text=f"System ID: {self.hid} | Created on {self.created.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        embed.timestamp = self.created

        return embed

    @staticmethod
    async def fetch_from_user(
        conn: asyncpg.Connection, user_id: hikari.Snowflake
    ) -> Optional["System"]:
        """Fetches a system from a user ID."""

        sql = """select systems.*,
        array(select uid from accounts where system = (select system from accounts where uid = $1)) as accounts,
        (select count(*) from members where system = (select system from accounts where uid = $1)) as member_count
        from systems where id = (select system from accounts where uid = $1)"""

        row = await conn.fetchrow(sql, user_id)

        return System(**row) if row else None

    @staticmethod
    async def fetch_from_hid(conn: asyncpg.Connection, hid: str):
        """Fetches a system from an ID."""

        pass

    @staticmethod
    async def has_system(conn: asyncpg.Connection, user_id: hikari.Snowflake) -> bool:
        """Returns true if the user has a system."""

        val: bool = await conn.fetchval(
            "select exists(select * from accounts where uid = $1)", user_id
        )
        return val

    @staticmethod
    async def create_system(
        conn: asyncpg.Connection, user_id: hikari.Snowflake, name: Optional[str] = None
    ) -> "System":
        """Creates a system."""

        async with conn.transaction():
            row = await conn.fetchrow(
                "insert into systems (hid, name) values (find_free_system_hid(), $1) returning *",
                name,
            )
            sys = System(**row)

            await conn.execute(
                "insert into accounts (system, uid) values ($1, $2)", sys.id, user_id
            )

            return sys
