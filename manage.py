#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import atexit
import os
import sys


def exit_handler():
    print("Cleaning up ngrok file...")
    file_path = ".ngrok"
    if os.path.exists(file_path):
        os.remove(file_path)


def main():
    if (
        os.getenv("NGROK_LISTENER_RUNNING") is None
        and os.getenv("NGROK_AUTHTOKEN") is not None
        and len(sys.argv) > 1
        and sys.argv[1] == "runserver"
    ):
        os.environ["NGROK_LISTENER_RUNNING"] = "true"
        import asyncio, ngrok  # noqa: E401, I001

        async def setup():
            listen = sys.argv[2] if len(sys.argv) > 2 else "localhost:8000"  # noqa: PLR2004
            try:
                listener = await ngrok.default()
                print(f"Forwarding to {listen} from ingress url: {listener.url()}")
                listener.forward(listen)
                with open(".ngrok", "w") as f:
                    f.write(listener.url())
                atexit.register(exit_handler)
            except ValueError:
                pass

        asyncio.run(setup())

    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "runtimeexceptions.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
