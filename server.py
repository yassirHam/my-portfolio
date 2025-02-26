from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from email.env
dotenv_path = Path('.') / 'email.env'  # Specify the correct filename
load_dotenv(dotenv_path=dotenv_path)

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

print(f"Email: {EMAIL_USER}")  # Should print your email, not None!

from flask import Flask, request, jsonify
from flask_mail import Mail, Message

app = Flask(__name__)

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_USER  # Use the loaded variable
app.config['MAIL_PASSWORD'] = EMAIL_PASS  # Use the loaded variable

mail = Mail(app)

@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    mobile = data.get("mobile")
    subject = data.get("subject")
    message = data.get("message")

    try:
        msg = Message(subject=f"New Contact Form Submission: {subject}",
                      sender=email,
                      recipients=[EMAIL_USER],  # Send to your email
                      body=f"Name: {name}\nEmail: {email}\nMobile: {mobile}\n\nMessage:\n{message}")
        mail.send(msg)
        return jsonify({"message": "Email sent successfully!"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to send email", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
