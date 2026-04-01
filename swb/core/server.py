"""Local development server."""

import os
import functools
from http.server import HTTPServer, SimpleHTTPRequestHandler

from swb.core.logger import get_logger

logger = get_logger("server")

DEFAULT_PORT = 8080


def run_dev_server(directory, port=DEFAULT_PORT):
    """Serve a directory over HTTP on localhost.

    Args:
        directory: Path to the directory to serve
        port: Port number (default 8080)
    """
    handler = functools.partial(SimpleHTTPRequestHandler, directory=directory)

    server = HTTPServer(("localhost", port), handler)
    logger.info("Serving %s at http://localhost:%d", directory, port)
    logger.info("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logger.info("Server stopped.")
