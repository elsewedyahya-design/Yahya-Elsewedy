"""Local Flask web UI for the Busway Offer Generator.

Two role-separated areas (blueprint §1):
  * User  (/)        — generate offers; cannot change product definitions.
  * Admin (/admin)   — manage products, ratings, standard text, images.

Run:  python -m busway.webapp     (then open http://127.0.0.1:5000)
"""
from .app import create_app  # noqa: F401
