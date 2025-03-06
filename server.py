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
nltk.data.path.append("./nltk_data")
nltk.download('punkt', download_dir="./nltk_data", quiet=True)
nltk.download('stopwords', download_dir="./nltk_data", quiet=True)

app = Flask(__name__)
CORS(app, resources={
  r"/chat": {"origins": "https://yassirham.github.io"},
  r"/send-message": {"origins": "https://yassirham.github.io"}
})

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")
mail = Mail(app)

CORS(app, resources={
    r"/chat": {
        "origins": "https://yassirham.github.io",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    },
    r"/send-message": {
        "origins": "https://yassirham.github.io",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})


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
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in tokens if word not in stop_words]
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

      query_vec = self.vectorizer.transform([self._preprocess(query)])
      scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
      best_match = self.answer_bank[np.argmax(scores)]
      return best_match if scores.max() > 0.2 else "Could you please rephrase your question?"

    except Exception as e:
      return f"Error processing request: {str(e)}"

  def _format_skills(self):
    skills = self.dataset[0]['skills']
    return "<span style='font-size: 1.1rem; line-height: 1.5;'>Skills:<br>" + \
           "<br>".join([f"• <strong>{k}</strong>: {', '.join(v)}" for k, v in skills.items()]) + \
           "</span>"

  def _format_projects(self):
    projects = self.dataset[0]['projects']
    return "<span style='font-size: 1.1rem; line-height: 1.5;'>Projects:<br>" + \
           "<br>".join([f"• <strong>{p['title']}</strong><br>&nbsp;&nbsp;{p['description']}" for p in projects]) + \
           "</span>"
  def _format_projects(self):
    projects = self.dataset[0]['projects']
    return "Projects:\n" + "\n".join([f"- {p['title']}: {p['description']}" for p in projects])

  def _format_experiences(self):
    experiences = self.dataset[0]['experiences']
    return "Experience:\n" + "\n".join([f"- {e['position']} at {e['company']}" for e in experiences])


chatbot = ChatBot()

@app.route("/chat", methods=["POST"])
def handle_chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Invalid request format"}), 400

        response = jsonify({"response": chatbot.get_response(data['message'])})
        response.headers.add("Access-Control-Allow-Origin", "https://yassirham.github.io")
        return response

    except Exception as e:
        error_response = jsonify({"error": str(e)})
        error_response.headers.add("Access-Control-Allow-Origin", "https://yassirham.github.io")
        return error_response, 500


@app.route("/send-message", methods=["OPTIONS"])
def message_preflight():
    return _build_cors_preflight_response()

def _build_cors_preflight_response():
    response = jsonify({"status": "preflight"})
    response.headers.add("Access-Control-Allow-Origin", "https://yassirham.github.io")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    return response

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
