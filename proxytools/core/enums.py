import enum
import typing


class Enum(enum.Enum):
    """Base enum class"""

    @classmethod
    def get(
        cls, item: str, fallback: typing.Optional[__qualname__] = None
    ) -> __qualname__:
        try:
            return cls.__dict__[item.upper()]
        except KeyError:
            if fallback is None:
                raise
            return fallback


class Privacy(Enum):
    """System/member privacy"""

    PUBLIC = 1
    PRIVATE = 2


class AutoproxyMode(Enum):
    """Autoproxy mode for a server"""

    OFF = 1
    LATCH = 2
    FRONT = 3
    MEMBER = 4
