#!/usr/bin/env python3

# proxytools: a Discord proxy bot written in Python with Hikari
# Copyright (C) 2021 Starshine System
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import logging
import os
import configparser
from pathlib import Path

import core


def main():
    if os.name != "nt":
        import uvloop

        uvloop.install()

    config = configparser.ConfigParser()
    config.read("./proxytools.ini")

    bot = core.Proxytools(
        config["bot"]["token"],
        config["bot"]["prefixes"].split(","),
        config["database"].get("url", None),
    )

    db_log = core.getLogger("database", logging.INFO)

    migrations = []
    for file in Path("proxytools/core/sql/migrations").iterdir():
        if file.is_file():
            migrations.append((file.name, file.read_text()))

    migrations.sort(key=lambda m: m[0])
    migrations = [m[1] for m in migrations]

    loop = asyncio.get_event_loop()

    applied = loop.run_until_complete(bot.run_migrations(migrations))
    if applied != 0:
        db_log.info(f"Applied {applied} migration(s)!")

    clean = Path("proxytools/core/sql/clean.sql").read_text()
    loop.run_until_complete(bot.db.execute(clean))
    db_log.info(f"Cleaned existing functions and views.")

    funcs = Path("proxytools/core/sql/functions.sql").read_text()
    loop.run_until_complete(bot.db.execute(funcs))
    db_log.info(f"Created SQL functions")

    bot.run()


if __name__ == "__main__":
    main()
