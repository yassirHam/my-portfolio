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

load_dotenv()
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")
mail = Mail(app)


class ChatBot:
  def __init__(self):
    with open('dataset.json', 'r') as f:
      self.dataset = json.load(f)
    self.corpus = []
    self.answer_bank = []
    self.categories = ['skills', 'education', 'projects', 'experiences']
    self.vectorizer = TfidfVectorizer()
    self._prepare_data()

  def _prepare_data(self):
    for category in self.categories:
      category_data = self.dataset[0][category]
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
    return ' '.join([word for word in tokens if word not in stopwords.words('english')])

  def get_response(self, query):
    query_clean = self._preprocess(query)
    if 'skill' in query.lower():
      skills = self.dataset[0]['skills']
      return "Skills:\n" + "\n".join([f"- {k}: {', '.join(v)}" for k, v in skills.items()])
    elif 'education' in query.lower():
      education = self.dataset[0]['education']
      return "Education:\n" + "\n".join([f"- {e['degree']} ({e['years']})" for e in education])
    elif 'project' in query.lower():
      projects = self.dataset[0]['projects']
      return "Projects:\n" + "\n".join([f"- {p['title']}: {p['description']}" for p in projects])
    elif 'experience' in query.lower():
      experiences = self.dataset[0]['experiences']
      return "Experience:\n" + "\n".join([f"- {e['position']} at {e['company']}" for e in experiences])
    query_vec = self.vectorizer.transform([query_clean])
    scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
    return self.answer_bank[np.argmax(scores)]


chatbot = ChatBot()


@app.route("/")
def home():
  return jsonify({"message": "Backend is running!"}), 200


@app.route("/send-message", methods=["OPTIONS", "POST"])
def send_email():
  if request.method == "OPTIONS":
    return jsonify({"message": "CORS preflight OK"}), 200
  try:
    data = request.json
    msg = Message(subject=f"New Contact: {data.get('subject')}",
                  sender=data.get('email'),
                  recipients=[os.getenv("EMAIL_USER")],
                  body=f"Name: {data.get('name')}\nEmail: {data.get('email')}\nMobile: {data.get('mobile')}\n\nMessage:\n{data.get('message')}")
    mail.send(msg)
    return jsonify({"message": "Email sent successfully!"}), 200
  except Exception as e:
    return jsonify({"message": "Failed to send email", "error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def handle_chat():
  try:
    data = request.json
    return jsonify({"response": chatbot.get_response(data.get('message'))}), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port, debug=True)
