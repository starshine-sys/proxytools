import typing

from lightbulb.checks import T_inv

from .bot import Context
from .system import System
from .error import UserError


async def _has_system(ctx: Context):
    if not await System.has_system(ctx.db, ctx.author.id):
        raise await ctx.errors.no_system(ctx, ctx.author)
    return True


async def _not_has_system(ctx: Context):
    if await System.has_system(ctx.db, ctx.author.id):
        user = ctx.bot.get_me()
        raise UserError(
            f"You already have a system registered with {user.username}. Type `{ctx.prefix}system` to view it."
        )
    return True


def has_system() -> typing.Callable[[T_inv], T_inv]:
    def decorate(command: T_inv) -> T_inv:
        command.add_check(_has_system)
        return command

    return decorate


def not_has_system() -> typing.Callable[[T_inv], T_inv]:
    def decorate(command: T_inv) -> T_inv:
        command.add_check(_not_has_system)
        return command

    return decorate
