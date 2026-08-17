"""StreamFlow desktop entry point."""
from __future__ import annotations

import sys

try:
    from .app import StreamFlow, main
except ImportError:
    from app import StreamFlow, main


__all__ = ["StreamFlow", "main"]


if __name__ == "__main__":
    sys.exit(main())
