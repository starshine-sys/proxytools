import hikari
import lightbulb


class UserError(lightbulb.errors.CommandError):
    """Catch-all for custom user errors."""

    _msg: str

    def __init__(self, msg: str):
        super().__init__(msg)
        self._msg = msg

    def __str__(self) -> str:
        return self._msg


class StringOverboundError(UserError):
    def __init__(self, subj: str, input: str, limit: int):
        super().__init__(f"{subj.title()} too long: {len(input)} > {limit} characters.")


class NoSystemError(UserError):
    def __init__(
        self,
        user: hikari.User,
        invoker: bool = False,
        bot_name: str = "proxytools",
        prefix: str = "pt;",
    ):
        if invoker:
            super().__init__(
                f"You do not have a system registered with {bot_name}. Create one with `{prefix}system new`."
            )
        else:
            super().__init__(
                f"**{user.username}#{user.discriminator}** does not have a system registered with {bot_name}."
            )
