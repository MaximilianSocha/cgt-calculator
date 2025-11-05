from flask import Flask, request, jsonify, send_file, render_template
from cgt_calculator import CGTCalculator
from output_excel_writer import export_capital_gains_to_excel
from werkzeug.utils import secure_filename
import os
import stripe
from datetime import datetime
import uuid

app = Flask(__name__)

# Configuration
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "outputs"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Stripe configuration
stripe.api_key = "your-stripe-secret-key"  # Set this in environment variable
STRIPE_PUBLISHABLE_KEY = "your-stripe-publishable-key"

# Ensure folders exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

# Store processed files temporarily (in production, use Redis or database)
processed_files = {}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "csv"


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
        return jsonify({"error": "Only CSV files are allowed"}), 400

    allow_short_selling = (
            True
            if "allow_short_selling" in request.form
            and bool(request.form["allow_short_selling"])
            else False
        )

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

        # Generate Excel file
        excel_filename = f"cgt_report_{session_id}.xlsx"
        excel_path = os.path.join(app.config["OUTPUT_FOLDER"], excel_filename)
        export_capital_gains_to_excel(data_dict, excel_path)

        # Store file info for later retrieval
        processed_files[session_id] = {
            "excel_path": excel_path,
            "excel_filename": excel_filename,
            "created_at": datetime.now().isoformat(),
        }

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
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500


@app.route("/api/create-payment-intent", methods=["POST"])
def create_payment_intent():
    """Create a Stripe payment intent"""
    data = request.json
    session_id = data.get("session_id")

    if not session_id or session_id not in processed_files:
        return jsonify({"error": "Invalid session"}), 400

    try:
        # Create payment intent with Stripe
        intent = stripe.PaymentIntent.create(
            amount=999,  # $9.99 in cents - adjust as needed
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

    if not session_id or session_id not in processed_files:
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
    if session_id not in processed_files:
        return jsonify({"error": "File not found or session expired"}), 404

    file_info = processed_files[session_id]
    excel_path = file_info["excel_path"]

    if not os.path.exists(excel_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(
        excel_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=file_info["excel_filename"],
    )


@app.route("/api/config")
def get_config():
    """Get Stripe publishable key for frontend"""
    return jsonify({"stripePublishableKey": STRIPE_PUBLISHABLE_KEY})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
