from flask import Flask, request, jsonify, send_file, render_template
from cgt_calculator import CGTCalculator
from output_excel_writer import export_capital_gains_to_excel
from werkzeug.utils import secure_filename
import os
import stripe
from datetime import datetime, timedelta
import uuid
import sqlite3
from contextlib import contextmanager
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Configuration
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "outputs"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["DATABASE"] = "sessions.db"

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

# Ensure folders exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

sqlite3.register_adapter(datetime, lambda val: val.isoformat())


# Database setup
def init_db():
    """Initialize the database with the sessions table"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                excel_path TEXT NOT NULL,
                excel_filename TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)
        conn.commit()


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def cleanup_old_sessions():
    """Remove sessions older than 24 hours and their associated files"""
    cutoff_time = datetime.now() - timedelta(hours=24)

    with get_db() as conn:
        # Get sessions to delete
        cursor = conn.execute(
            "SELECT session_id, excel_path FROM sessions WHERE created_at < ?",
            (cutoff_time,),
        )
        old_sessions = cursor.fetchall()

        # Delete files and database records
        for session in old_sessions:
            excel_path = os.path.join(os.getcwd(), session["excel_path"])
            if os.path.exists(excel_path):
                try:
                    os.remove(excel_path)
                    print(f"Deleted old file: {excel_path}")
                except Exception as e:
                    print(f"Error deleting file {excel_path}: {e}")

        # Delete from database
        conn.execute("DELETE FROM sessions WHERE created_at < ?", (cutoff_time,))
        deleted_count = conn.total_changes
        conn.commit()

        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old session(s)")


def store_session(session_id, excel_path, excel_filename):
    """Store session information in the database"""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO sessions (session_id, excel_path, excel_filename, created_at)
               VALUES (?, ?, ?, ?)""",
            (session_id, excel_path, excel_filename, datetime.now()),
        )
        conn.commit()


def get_session(session_id):
    """Retrieve session information from the database"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "session_id": row["session_id"],
                "excel_path": row["excel_path"],
                "excel_filename": row["excel_filename"],
                "created_at": row["created_at"],
            }
        return None


def session_exists(session_id):
    """Check if a session exists in the database"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE session_id = ?", (session_id,)
        )
        return cursor.fetchone()[0] > 0


def allowed_file(filename):
    extension = filename.rsplit(".", 1)[1].lower()
    return "." in filename and (extension == "csv" or extension == "xlsx")


# Initialize database
init_db()

# Set up background scheduler for cleanup
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_sessions, trigger="interval", hours=1)
scheduler.start()

# Shutdown scheduler when app exits
atexit.register(lambda: scheduler.shutdown())


@app.route("/")
def index():
    """Serve the HTML frontend"""
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle CSV file upload and processing"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only CSV and XLSX files are allowed"}), 400

    allow_short_selling = (
        True
        if "allow_short_selling" in request.form
        and bool(request.form["allow_short_selling"])
        else False
    )

    csv_path = None
    try:
        # Generate unique ID for this processing session
        session_id = str(uuid.uuid4())

        # Save uploaded file
        filename = secure_filename(file.filename)
        csv_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{session_id}_{filename}")
        file.save(csv_path)

        # Calculate the optimal capital gains tax for each financial year
        try:
            data_dict = CGTCalculator(csv_path).execute(allow_short_selling)
        except ValueError as e:
            return jsonify({"short_sell_warning": str(e)}), 300
        except RuntimeError as e:
            error_lines = str(e).split("\n")
            return jsonify(
                {
                    "symbol_error": error_lines[0],
                    "lp_error": error_lines[1],
                }
            ), 300

        # Generate Excel file
        excel_filename = f"cgt_report_{session_id}.xlsx"
        excel_path = os.path.join(app.config["OUTPUT_FOLDER"], excel_filename)
        export_capital_gains_to_excel(data_dict, excel_path)

        # Store session info in database
        store_session(session_id, excel_path, excel_filename)

        # Clean up CSV file
        os.remove(csv_path)

        return jsonify(
            {
                "success": True,
                "message": "Your CGT report has been generated successfully!",
                "session_id": session_id,
                "summary": {
                    "years_processed": len(data_dict),
                    "financial_years": list(int(year) for year in data_dict.keys()),
                },
            }
        )

    except Exception as e:
        # Clean up CSV file on error
        if csv_path and os.path.exists(csv_path):
            os.remove(csv_path)
        return jsonify({"error": str(e)}), 500


@app.route("/api/create-payment-intent", methods=["POST"])
def create_payment_intent():
    """Create a Stripe payment intent"""
    data = request.json
    session_id = data.get("session_id")

    if not session_id or not session_exists(session_id):
        return jsonify({"error": "Invalid session"}), 400

    try:
        # Create payment intent with Stripe
        intent = stripe.PaymentIntent.create(
            amount=1999,  # $19.99 in cents
            currency="aud",
            metadata={"session_id": session_id},
        )

        return jsonify(
            {
                "clientSecret": intent.client_secret,
                "publishableKey": STRIPE_PUBLISHABLE_KEY,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/verify-payment", methods=["POST"])
def verify_payment():
    """Verify payment and provide download"""
    data = request.json
    payment_intent_id = data.get("payment_intent_id")
    session_id = data.get("session_id")

    if not session_id or not session_exists(session_id):
        return jsonify({"error": "Invalid session"}), 400

    try:
        # Verify payment with Stripe
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status == "succeeded":
            return jsonify(
                {"success": True, "download_url": f"/api/download/{session_id}"}
            )
        else:
            return jsonify({"error": "Payment not completed"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<session_id>")
def download_file(session_id):
    """Download the generated Excel file"""
    session = get_session(session_id)

    if not session:
        return jsonify({"error": "File not found or session expired"}), 404

    excel_path = os.path.join(os.getcwd(), session["excel_path"])

    if not os.path.exists(excel_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(
        excel_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=session["excel_filename"],
    )


@app.route("/api/config")
def get_config():
    """Get Stripe publishable key for frontend"""
    return jsonify({"stripePublishableKey": STRIPE_PUBLISHABLE_KEY})


@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        with get_db() as conn:
            conn.execute("SELECT 1")
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/api/cleanup", methods=["POST"])
def manual_cleanup():
    """Manually trigger cleanup (for admin use)"""
    try:
        cleanup_old_sessions()
        return jsonify({"success": True, "message": "Cleanup completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
