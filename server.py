from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_cors import CORS  # Import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r"/send-email": {"origins": "https://yassirham.github.io"}})

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")  # Your email
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")  # Your app password

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
                      recipients=[os.getenv("EMAIL_USER")],
                      body=f"Name: {name}\nEmail: {email}\nMobile: {mobile}\n\nMessage:\n{message}")
        mail.send(msg)
        return jsonify({"message": "Email sent successfully!"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to send email", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
