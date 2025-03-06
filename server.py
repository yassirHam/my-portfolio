from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import time

load_dotenv()
nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))

nltk.download('punkt', download_dir='nltk_data', quiet=True)
nltk.download('stopwords', download_dir='nltk_data', quiet=True)

app = Flask(__name__)
CORS(app, resources={
  r"/chat": {
    "origins": "https://yassirham.github.io",
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
  },
  r"/send-message": {
    "origins": "https://yassirham.github.io",
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
  }
})

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")
mail = Mail(app)


class ChatBot:
  def __init__(self):
    self.dataset = self._load_dataset()
    self.corpus = []
    self.answer_bank = []
    self.categories = ['skills', 'education', 'projects', 'experiences']
    self.vectorizer = TfidfVectorizer()
    self._prepare_data()

  def _load_dataset(self):
    try:
      with open('dataset.json', 'r') as f:
        return json.load(f)
    except Exception as e:
      raise RuntimeError(f"Failed to load dataset: {str(e)}")

  def _prepare_data(self):
    for category in self.categories:
      category_data = self.dataset[0].get(category, {})
      if isinstance(category_data, dict):
        for subcategory, items in category_data.items():
          combined_text = ' '.join(items)
          self.corpus.append(self._preprocess(combined_text))
          self.answer_bank.append(f"{subcategory}: {', '.join(items)}")
      elif isinstance(category_data, list):
        for item in category_data:
          text_parts = []
          answer_parts = []
          for key, value in item.items():
            if isinstance(value, list):
              text_parts.extend(value)
              answer_parts.append(f"{key}: {', '.join(value)}")
            elif isinstance(value, str):
              text_parts.append(value)
              answer_parts.append(f"{key}: {value}")
          self.corpus.append(self._preprocess(' '.join(text_parts)))
          self.answer_bank.append(' | '.join(answer_parts))
    self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)

  def _preprocess(self, text):
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text.lower())
    tokens = word_tokenize(text)
    filtered_words = [word for word in tokens if word not in stopwords.words('english')]
    return ' '.join(filtered_words)

  def get_response(self, query):
    try:
      query = query.lower().strip()
      if 'skill' in query:
        return self._format_skills()
      elif 'education' in query:
        return self._format_education()
      elif 'project' in query:
        return self._format_projects()
      elif 'experience' in query:
        return self._format_experiences()
      if any(word in query for word in ["hire", "choose", "select"]):
        return self._format_why_hire()
      elif "strength" in query:
        return self._format_strengths()
      elif "weakness" in query:
        return "I tend to deeply focus on solving complex problems, which I manage through timeboxing and regular progress checks"
      elif "goal" in query or "objective" in query:
        return self._format_career_goals()
      elif "challenge" in query:
        return self._format_challenge()
      elif "failure" in query:
        return self._format_failure()
      elif "success" in query:
        return self._format_success()
      elif "contact" in query or "reach" in query:
        return self._format_contact_info()
      elif "salary" in query:
        return "I'm open to discussion based on industry standards and the total compensation package"
      query_vec = self.vectorizer.transform([self._preprocess(query)])
      scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
      best_match = self.answer_bank[np.argmax(scores)]
      return best_match if scores.max() > 0.2 else "Could you please rephrase your question?"

    except Exception as e:
      return f"Error processing request: {str(e)}"

  def _format_skills(self):
    skills = self.dataset[0]['skills']
    return "<strong>Skills:</strong><br>" + "<br>".join([f"• {k}: {', '.join(v)}" for k, v in skills.items()])

  def _format_education(self):
    education = self.dataset[0]['education']
    return "<strong>Education:</strong><br>" + "<br>".join([f"• {e['degree']} ({e['years']})" for e in education])

  def _format_projects(self):
    projects = self.dataset[0]['projects']
    return "<strong>Projects:</strong><br>" + "<br>".join([f"• {p['title']}<br>  {p['description']}" for p in projects])

  def _format_experiences(self):
    experiences = self.dataset[0]['experiences']
    return "<strong>Experience:</strong><br>" + "<br>".join(
      [f"• {e['position']} at {e['company']}" for e in experiences])

  def _format_why_hire(self):
    points = self.dataset[0]['hr_questions']['why_hire']
    return "<strong>Why Hire Me:</strong><br>" + "<br>• ".join([""] + points)

  def _format_strengths(self):
    points = self.dataset[0]['hr_questions']['strengths']
    return "<strong>Key Strengths:</strong><br>" + "<br>• ".join([""] + points)

  def _format_career_goals(self):
    goals = self.dataset[0]['hr_questions']['career_goals']
    return "<strong>Career Goals:</strong><br>" + "<br>• ".join([""] + goals)

  def _format_contact_info(self):
    info = self.dataset[0]['personal_info']
    return f"""
         <strong>Contact Information:</strong><br>
         • 📧 Email: {info['email']}<br>
         • 📱 Phone: {info['phone']}<br>
         • 🌐 Portfolio: <a href="{info['portfolio']}" target="_blank">{info['portfolio']}</a>
         """

  def _format_challenge(self):
    return f"<strong>Biggest Challenge:</strong><br>{self.dataset[0]['interview_answers']['challenge']}"

  def _format_failure(self):
    return f"<strong>Learning from Failure:</strong><br>{self.dataset[0]['interview_answers']['failure']}"

  def _format_success(self):
    return f"<strong>Notable Success:</strong><br>{self.dataset[0]['interview_answers']['success']}"

  def _handle_general_query(self, query):
    query_vec = self.vectorizer.transform([self._preprocess(query)])
    scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
    best_match = self.answer_bank[np.argmax(scores)]
    return best_match if scores.max() > 0.2 else "Could you please rephrase your question?"

chatbot = ChatBot()


@app.route("/chat", methods=["OPTIONS", "POST"])
def handle_chat():
  start_time = time.time()
  try:
    if request.method == "OPTIONS":
      response = jsonify({"status": "preflight"})
      response.headers.add("Access-Control-Allow-Origin", "https://yassirham.github.io")
      response.headers.add("Access-Control-Allow-Headers", "Content-Type")
      response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
      return response

    data = request.get_json()
    if not data or 'message' not in data:
      return jsonify({"error": "Invalid request format"}), 400

    response_text = chatbot.get_response(data['message'])
    response = jsonify({"response": response_text})
    response.headers.add("Access-Control-Allow-Origin", "https://yassirham.github.io")
    app.logger.info(f"Response time: {time.time() - start_time:.2f}s")
    return response

  except Exception as e:
    app.logger.error(f"Chat error: {str(e)}")
    error_response = jsonify({"error": "Internal server error"})
    error_response.headers.add("Access-Control-Allow-Origin", "https://yassirham.github.io")
    return error_response, 500


@app.route("/send-message", methods=["OPTIONS", "POST"])
def send_email():
    if request.method == "OPTIONS":
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
        print("Error:", str(e))
        return jsonify({"message": "Failed to send email", "error": str(e)}), 500


if __name__ == "__main__":
  nltk.download('punkt', download_dir='nltk_data', quiet=True)
  nltk.download('stopwords', download_dir='nltk_data', quiet=True)
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
