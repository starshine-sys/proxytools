import asyncio
import enum
import logging
import typing
from typing import List, Optional, Union

import hikari
import asyncpg
import lightbulb
from hikari import Intents

from .webhook import WebhookCache
from .log import getLogger
from .error import *

extensions = ["commands.system"]


class Proxytools(lightbulb.Bot):
    _db: asyncpg.Connection
    _log: logging.Logger

    webhooks: WebhookCache
    errors: "ErrorManager"

    class Colour:
        DEFAULT = hikari.Colour.from_int(0x51A8E2)
        SUCCESS = hikari.Colour.from_int(0x2ECC71)
        WARNING = hikari.Colour.from_int(0xE67E22)
        ERROR = hikari.Colour.from_int(0xE74C3C)
        EMPTY = hikari.Colour.from_int(0)

    def __init__(
        self,
        token: str,
        prefixes: List[str],
        db_url: str,
        **kwargs,
    ):
        self._log = getLogger("proxytools", logging.DEBUG)

        intents = (
            Intents.GUILDS
            | Intents.GUILD_MESSAGES
            | Intents.GUILD_MESSAGE_REACTIONS
            | Intents.DM_MESSAGES
            | Intents.DM_MESSAGE_REACTIONS
            | Intents.GUILD_WEBHOOKS
        )

        guild_id = kwargs.pop("guild_id", None)
        guild_id: int = int(guild_id) if guild_id else None

        super().__init__(
            token=token,
            intents=intents,
            insensitive_commands=True,
            prefix=prefixes,
            **kwargs,
        )

        self.webhooks = WebhookCache(self)
        self.errors = ErrorManager(self)

        loop = asyncio.get_event_loop()
        self._db = loop.run_until_complete(asyncpg.connect(db_url))

        for ext in extensions:
            try:
                self.load_extension(ext)
                self.log.info(f'Loaded extension "{ext}"')
            except Exception as e:
                self.log.error(f'Error loading extension "{ext}"')
                self.log.exception(e)

    async def run_migrations(
        self, migrations: List[str], logger: logging.Logger = None
    ) -> int:
        """Runs the needed migrations. Returns the number of applied migrations."""

        logger = logger or self._log

        # noinspection PyBroadException
        try:
            current: int = await self._db.fetchval("select schema_version from info")
        except:
            current: int = 0

        if len(migrations) <= current:
            return 0

        applied = 0
        async with self._db.transaction():
            for m in migrations[current:]:
                # noinspection PyBroadException
                try:
                    await self._db.execute(m)
                    logger.info(f"Executed migration {current + 1}")
                    current += 1
                    applied += 1
                except Exception as e:
                    logger.error(f"Error executing migration {current + 1}")
                    logger.exception(e)

        return applied

    def get_context(
        self,
        message: hikari.Message,
        prefix: str,
        invoked_with: str,
        invoked_command: lightbulb.Command,
    ) -> "Context":
        return Context(self, message, prefix, invoked_with, invoked_command)

    @property
    def db(self) -> asyncpg.Connection:
        return self._db

    @property
    def log(self) -> logging.Logger:
        return self._log


class Context(lightbulb.Context):
    _db: asyncpg.Connection
    _errors: "ErrorManager"

    class Colour(Proxytools.Colour):
        pass

    def __init__(
        self,
        bot: Proxytools,
        message: hikari.Message,
        prefix: str,
        invoked_with: str,
        command: lightbulb.Command,
    ) -> None:
        super().__init__(bot, message, prefix, invoked_with, command)
        self._db = bot.db
        self._errors = bot.errors

    async def reply(
        self,
        content: str,
        *,
        title: str = None,
        colour: hikari.Colour = None,
        footer: str = None,
    ) -> hikari.Message:
        """Reply to the user in a fancy embed."""
        embed = hikari.Embed(
            description=content, colour=colour if colour else self.Colour.DEFAULT
        )
        if title:
            embed.title = title
        if footer:
            embed.set_footer(text=footer)

        return await self.respond(embeds=[embed])

    async def prompt(
        self,
        prompt: str,
        *,
        colour: hikari.Colour = None,
        timeout: Union[float, int, None] = 60,
    ) -> (bool, bool, hikari.Message):
        """Prompts the user for `prompt` and lets them react to choose yes or no.
        Returns:
        - True if confirmed, False if cancelled
        - True if timed out, False if not timed out
        - the confirmation message"""

        msg = await self.reply(prompt, colour=colour)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(ev: hikari.ReactionAddEvent):
            return ev.user_id == self.author.id and ev.emoji_name in ("✅", "❌")

        try:
            event: hikari.ReactionAddEvent = await self.bot.wait_for(
                hikari.ReactionAddEvent, timeout, check
            )
        except TimeoutError:
            return False, True, msg

        return event.emoji_name == "✅", False, msg

    @property
    def db(self) -> asyncpg.Connection:
        return self._db

    @property
    def errors(self) -> "ErrorManager":
        return self._errors


class ErrorManager:
    """Class with methods for raising error with messages containing dynamic parameters
    (such as bot name or prefixes)"""

    _app: hikari.GatewayBotAware
    _user: hikari.OwnUser = None

    def __init__(self, bot: hikari.GatewayBotAware):
        self._app = bot

    def no_system(self, ctx: Context, user: hikari.User) -> NoSystemError:
        if self._user is None:
            self._user = self._app.get_me()

        return NoSystemError(
            user,
            (ctx.author.id == user.id),
            bot_name=self._user.username,
            prefix=ctx.prefix,
        )
