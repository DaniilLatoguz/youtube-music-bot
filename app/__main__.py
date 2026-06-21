"""Entry point: ``python -m app``."""

import sys

from pydantic import ValidationError


def main() -> None:
    try:
        # Importing the bot triggers settings loading; a missing BOT_TOKEN /
        # ADMIN_ID raises ValidationError, which we turn into a clear message.
        from app.bot import run
    except ValidationError as exc:
        sys.exit(
            "Configuration error: required settings are missing.\n"
            "Make sure your .env file contains BOT_TOKEN and ADMIN_ID "
            "(see .env.example).\n\n"
            f"{exc}"
        )
    run()


if __name__ == "__main__":
    main()
