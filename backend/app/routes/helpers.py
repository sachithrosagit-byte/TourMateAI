"""Small shared helpers for the web/business routes.

Keeps the JSON error shape identical across every endpoint so the frontend can
rely on a single ``{ "error": <message> }`` contract (see docs/api-contract.md
§Conventions).
"""

from flask import jsonify


def json_error(message, status):
    """Return a ``({"error": message}, status)`` tuple for a Flask handler.

    Usage::

        return json_error("Attraction not found.", 404)
    """
    return jsonify({"error": message}), status
