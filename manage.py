"""CLI for the Sunbreeze application."""

import argparse
from wsgiref.simple_server import make_server

from loguru import logger

from sunbreeze.app import app


def start_server() -> None:
    """Start the development server. Should not be used in production."""
    logger.info("Starting development server on http://localhost:8000")
    make_server(host="localhost", port=8000, app=app).serve_forever()


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
