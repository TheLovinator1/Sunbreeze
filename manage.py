"""CLI for the Sunbreeze application."""

import argparse
import logging
import logging.config

import uvicorn

logger: logging.Logger = logging.getLogger(name="uvicorn.error")


def start_server() -> None:
    """Start the development server. Should not be used in production."""
    logger.info("Starting development server on http://localhost:8000")
    uvicorn.run(app="sunbreeze.main:app", host="127.0.0.1", port=8000, log_level="debug", reload=True, factory=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--startserver",
        action="store_true",
        help="Start the development server.",
    )
    args: argparse.Namespace = parser.parse_args()

    if args.startserver:
        start_server()
    else:
        parser.print_help()
