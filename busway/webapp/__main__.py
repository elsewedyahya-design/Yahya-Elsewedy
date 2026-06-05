"""Launch the local web UI:  python -m busway.webapp"""
from . import create_app

if __name__ == "__main__":
    app = create_app()
    print("Busway Offer Generator — open http://127.0.0.1:5000")
    print("Admin area at /admin (default password 'admin'; set "
          "BUSWAY_ADMIN_PASSWORD to change).")
    app.run(host="127.0.0.1", port=5000, debug=False)
