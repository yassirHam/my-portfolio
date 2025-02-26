from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes (Debug mode: allows all origins)
CORS(app, resources={r"/*": {"origins": "*"}})

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")

mail = Mail(app)

@app.route("/")
def home():
    return jsonify({"message": "Backend is running!"}), 200

@app.route("/send-message", methods=["OPTIONS", "POST"])
def send_email():
    if request.method == "OPTIONS":
        # Handle preflight request (CORS check)
        return jsonify({"message": "CORS preflight OK"}), 200

    try:
        data = request.json
        name = data.get("name")
        email = data.get("email")
        mobile = data.get("mobile")
        subject = data.get("subject")
        message = data.get("message")

        if not name or not email or not message:
            return jsonify({"message": "Missing required fields"}), 400

        msg = Message(subject=f"New Contact Form Submission: {subject}",
                      sender=email,
                      recipients=[os.getenv("EMAIL_USER")],
                      body=f"Name: {name}\nEmail: {email}\nMobile: {mobile}\n\nMessage:\n{message}")
        mail.send(msg)

        return jsonify({"message": "Email sent successfully!"}), 200

    except Exception as e:
        print("Error:", str(e))  # Log error to backend
        return jsonify({"message": "Failed to send email", "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
