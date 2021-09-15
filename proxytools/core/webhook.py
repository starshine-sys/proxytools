from typing import Optional

import hikari


class WebhookCache:
    """A cache of webhooks used for proxying."""

    _cache: dict[hikari.Snowflake, hikari.ExecutableWebhook]
    _app: hikari.RESTAware
    _user: hikari.OwnUser = None

    def __init__(self, app: hikari.RESTAware):
        self._cache = dict()
        self._app = app

    async def get_for_channel(
        self, channel: hikari.Snowflake
    ) -> Optional[hikari.ExecutableWebhook]:
        """Gets the proxy webhook for the given channel."""

        try:
            return self._cache[channel]
        except KeyError:
            return await self._fetch_or_create(channel)

    async def _fetch_or_create(
        self, channel: hikari.Snowflake
    ) -> hikari.ExecutableWebhook:
        """Fetches or creates a webhook for the given channel."""

        if self._user is None:
            self._user = await self._app.rest.fetch_my_user()

        webhooks = await self._app.rest.fetch_channel_webhooks(channel)
        for wh in webhooks:
            if isinstance(wh, hikari.IncomingWebhook):
                if wh.author.id is self._user.id:
                    self._cache[channel] = wh
                    return wh

        # else, no webhook found, so create one
        wh = await self._app.rest.create_webhook(
            channel, f"{self._user.username} Webhook", reason="Create proxy webhook"
        )
        self._cache[channel] = wh
        return wh

    def delete(self, channel: hikari.Snowflake):
        """Clears the webhook cache for the given channel."""
        try:
            del self._cache[channel]
        except KeyError:
            pass
