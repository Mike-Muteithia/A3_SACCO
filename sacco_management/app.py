"""
Akiba Sacco Application Factory & Runtime Configuration
Configured for production WSGI deployment behind Nginx with structured logging,
strict CSRF protections, and resilient error recovery.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from decimal import Decimal

from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from models import db, User

# Load environment configuration
load_dotenv()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please authenticate to access the Akiba Sacco secure portal.'
login_manager.login_message_category = 'warning'
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


def setup_logging(app: Flask) -> None:
    """Configures multi-destination rotating file logs with fallback for WSL2 local dev."""
    log_formatter = logging.Formatter(
        '[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s in %(module)s:%(lineno)d] - %(message)s'
    )

    # Attempt primary system log directory; fall back gracefully in unprivileged development
    primary_log_dir = Path("/var/log/akiba_sacco")
    try:
        primary_log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = primary_log_dir / "app.log"
        file_handler = RotatingFileHandler(
            str(log_file_path), maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
        )
    except (PermissionError, OSError):
        fallback_log_dir = Path(app.root_path) / "logs"
        fallback_log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = fallback_log_dir / "app.log"
        file_handler = RotatingFileHandler(
            str(log_file_path), maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
        )

    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # In local debug mode, also mirror to stderr
    if app.debug or os.getenv('FLASK_ENV') == 'development':
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(log_formatter)
        stream_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(stream_handler)

    app.logger.info("Structured logging initialized successfully.")


def create_app(test_config=None) -> Flask:
    app = Flask(__name__)

    # --- Production Security & Environment Invariants ---
    env_mode = os.getenv('FLASK_ENV', 'production').lower()
    secret_key = os.getenv('SECRET_KEY')

    if not secret_key:
        if env_mode == 'production':
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR:\n"
                "The 'SECRET_KEY' environment variable is missing. Ephemeral fallbacks are strictly prohibited "
                "in production multi-worker environments to prevent session invalidation and CSRF failures."
            )
        # Consistent static key for WSL2 / Local Development (avoids per-worker session drift)
        app.logger.warning("DEVELOPMENT WARNING: Using static fallback SECRET_KEY. Set this in .env for production.")
        secret_key = "akiba-sacco-dev-static-fallback-key-do-not-use-in-prod"

    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql://akiba_admin:akiba_secure_pass@localhost:5432/akiba_sacco'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # Prevents mid-day session expiration on long active sessions
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    if test_config:
        app.config.update(test_config)

    # Configure Reverse Proxy Header Handling (Nginx -> Gunicorn)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Initialize Extensions
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    setup_logging(app)

    # Custom Jinja Template Filters
    @app.template_filter('currency')
    def format_currency(value) -> str:
        if value is None:
            return "KES 0.00"
        try:
            dec_val = Decimal(str(value))
            return f"KES {dec_val:,.2f}"
        except Exception:
            return f"KES {value}"

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.members import members_bp
    from routes.transactions import transactions_bp
    from routes.loans import loans_bp
    from routes.reports import reports_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    # Register Global HTTP Error Handlers
    @app.errorhandler(400)
    def handle_bad_request(e):
        app.logger.warning(f"400 Bad Request: {request.url} - {str(e)}")
        return render_template('base.html', error_code="400", error_title="Bad Request",
                               error_msg="The server could not process the request due to malformed data or invalid form tokens."), 400

    @app.errorhandler(403)
    def handle_forbidden(e):
        app.logger.warning(f"403 Forbidden: {request.url} - User: {getattr(request, 'remote_addr', 'N/A')}")
        return render_template('base.html', error_code="403", error_title="Access Forbidden",
                               error_msg="You do not hold the required RBAC permissions to view or perform operations on this resource."), 403

    @app.errorhandler(404)
    def handle_not_found(e):
        return render_template('base.html', error_code="404", error_title="Resource Not Found",
                               error_msg="The ledger record, profile, or endpoint requested could not be located."), 404

    @app.errorhandler(500)
    def handle_server_error(e):
        db.session.rollback()
        app.logger.error(f"500 Internal Server Error encountered at {request.url}", exc_info=True)
        return render_template('base.html', error_code="500", error_title="Internal System Error",
                               error_msg="A financial transaction failed safely. Database state has been rolled back automatically."), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)