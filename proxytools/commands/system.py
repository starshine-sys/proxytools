import logging
from typing import Optional, Union

import hikari
import lightbulb

import proxytools.core as core


class System(lightbulb.Plugin):
    _log: logging.Logger

    def __init__(self, bot: core.Proxytools):
        super().__init__(name="System")
        self._log = bot.log

    @lightbulb.group(aliases=["s"])
    async def system(
        self, ctx: core.Context, id: Optional[Union[hikari.User, str]] = None
    ):
        """View information about a system."""
        if id is None:
            return await self._own_system(ctx)

        await ctx.respond(f"Your input: {id}")

    async def _own_system(self, ctx: core.Context):
        sys = await core.System.fetch_from_user(ctx.db, ctx.author.id)
        if sys is None:
            raise ctx.errors.no_system(ctx, ctx.author)

        await ctx.respond(embed=await sys.embed(ctx))

    @core.not_has_system()
    @system.command(aliases=["create"])
    async def new(self, ctx: core.Context, *, name: str = None):
        """Create a system."""
        if name is not None and len(name) > core.Limits.SYSTEM_NAME_LIMIT:
            raise core.StringOverboundError(
                "description", name, core.Limits.SYSTEM_NAME_LIMIT
            )

        sys = await core.System.create_system(ctx.db, ctx.author.id, name)

        s = "Your system, "
        s += f"{sys.name} (`{sys.hid}`)" if sys.name is not None else f"`{sys.hid}`"
        s += f", has been created. Type `{ctx.prefix}system` to view it!"
        await ctx.reply(s, colour=ctx.Colour.SUCCESS)

    @core.has_system()
    @system.command(aliases=["desc"])
    async def description(self, ctx: core.Context, *, desc: str = None):
        """View, reset, or update your system's description."""

        sys = await core.System.fetch_from_user(ctx.db, ctx.author.id)

        if not desc:
            if not sys.description:
                return await ctx.reply(
                    f"Your system does not have a description set. Use `{ctx.prefix}system description <new description>` to set one!"
                )
            return await ctx.reply(
                sys.description,
                title="System description",
                footer=f"System ID: {sys.hid} | Use {ctx.prefix}description -clear to clear this description.",
            )

        if desc.lower() in ("-clear", "clear"):
            yes, timeout, _ = await ctx.prompt(
                "Are you sure you want to clear your system description?",
                colour=ctx.Colour.WARNING,
            )
            if timeout:
                return await ctx.reply("Timed out.")
            if not yes:
                return await ctx.reply("Cancelled.")

            await ctx.db.execute(
                "update systems set description = null where id = $1", sys.id
            )
            return await ctx.reply("System description cleared!")

        if len(desc) > core.Limits.DESCRIPTION_LIMIT:
            raise core.StringOverboundError(
                "description", desc, core.Limits.DESCRIPTION_LIMIT
            )

        await ctx.db.execute(
            "update systems set description = $1 where id = $2", desc, sys.id
        )
        return await ctx.reply("System description updated!")

    @lightbulb.listener()
    async def on_command_error(self, event: lightbulb.CommandErrorEvent) -> bool:
        if isinstance(event.exception, lightbulb.errors.CommandNotFound):
            return True

        elif isinstance(event.exception, core.UserError):
            await event.message.respond(f":x: {event.exception}")
            return True
        elif isinstance(
            event.exception,
            (lightbulb.errors.CommandError, lightbulb.errors.CommandSyntaxError),
        ):
            await event.message.respond(f":x: {event.exception}")
            return True

        await event.message.respond(":x: Internal error occurred.")

        self._log.error(f"Error in command {event.command}:")
        self._log.exception(event.exception)


def load(bot: core.Proxytools):
    bot.add_plugin(System(bot))
