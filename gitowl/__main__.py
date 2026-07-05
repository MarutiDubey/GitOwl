"""Enable `python -m gitowl` as an alias for the CLI."""

from gitowl.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
