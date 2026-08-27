"""TourMateAI AI package.

Self-contained AI feature package (recommender, chatbot, vision). The web/Flask
side mounts it as a Blueprint; the two sides meet only at the HTTP/JSON contracts
in docs/api-contract.md. See CLAUDE.md "Team Split & Ownership".
"""

from .blueprint import ai_bp

__all__ = ["ai_bp"]
