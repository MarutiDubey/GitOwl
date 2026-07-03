"""Enable `python -m devguard` as an alias for the CLI."""

from devguard.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
