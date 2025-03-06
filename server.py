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
from googletrans import Translator

load_dotenv()
nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))

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
        self.translator = Translator()
        self.dataset = self._load_dataset()
        self.corpus = []
        self.answer_bank = []
        self.categories = ['skills', 'education', 'projects', 'experiences']
        self.vectorizer = TfidfVectorizer()
        self._prepare_data()

    def _load_dataset(self):
        with open('dataset.json', 'r') as f:
            return json.load(f)

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

    def _translate(self, text, src_lang, dest_lang='en'):
        try:
            return self.translator.translate(text, src=src_lang, dest=dest_lang).text
        except Exception as e:
            app.logger.error(f"Translation error: {str(e)}")
            return text

    def get_response(self, query, lang='en'):
        try:
            detected = self.translator.detect(query)
            query_en = self._translate(query, detected.lang) if detected.lang != 'en' else query
            response_en = self._process_query(query_en)
            return self._translate(response_en, 'en', lang) if detected.lang != 'en' else response_en
        except Exception as e:
            app.logger.error(f"Chatbot error: {str(e)}")
            return "I encountered an error processing your request. Please try again."

    def _process_query(self, query):
        query = query.lower().strip()
        if any(word in query for word in ["hire", "choose", "select"]): return self._format_why_hire()
        if "strength" in query: return self._format_strengths()
        if "weakness" in query: return "I manage deep focus with timeboxing"
        if "goal" in query or "objective" in query: return self._format_career_goals()
        if "challenge" in query: return self._format_challenge()
        if "failure" in query: return self._format_failure()
        if "success" in query: return self._format_success()
        if "contact" in query or "reach" in query: return self._format_contact_info()
        if "salary" in query: return "Open to competitive offers"
        if 'skill' in query: return self._format_skills()
        if 'education' in query: return self._format_education()
        if 'project' in query: return self._format_projects()
        if 'experience' in query: return self._format_experiences()
        return self._handle_general_query(query)

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
        return "<strong>Experience:</strong><br>" + "<br>".join([f"• {e['position']} at {e['company']}" for e in experiences])

    def _format_why_hire(self):
        return "<strong>Why Hire Me:</strong><br>" + "<br>• ".join([""] + self.dataset[0]['hr_questions']['why_hire'])

    def _format_strengths(self):
        return "<strong>Strengths:</strong><br>" + "<br>• ".join([""] + self.dataset[0]['hr_questions']['strengths'])

    def _format_career_goals(self):
        return "<strong>Career Goals:</strong><br>" + "<br>• ".join([""] + self.dataset[0]['hr_questions']['career_goals'])

    def _format_contact_info(self):
        info = self.dataset[0]['personal_info']
        return f"""<strong>Contact:</strong><br>• 📧 {info['email']}<br>• 📱 {info['phone']}<br>• 🌐 <a href="{info['portfolio']}">Portfolio</a>"""

    def _format_challenge(self): return f"<strong>Challenge:</strong><br>{self.dataset[0]['interview_answers']['challenge']}"
    def _format_failure(self): return f"<strong>Failure Lesson:</strong><br>{self.dataset[0]['interview_answers']['failure']}"
    def _format_success(self): return f"<strong>Success Story:</strong><br>{self.dataset[0]['interview_answers']['success']}"

    def _handle_general_query(self, query):
        query_vec = self.vectorizer.transform([self._preprocess(query)])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        best_match = self.answer_bank[np.argmax(scores)]
        return best_match if scores.max() > 0.2 else "Please rephrase your question"

chatbot = ChatBot()

@app.route("/chat", methods=["POST"])
def handle_chat():
    try:
        data = request.get_json()
        response = jsonify({
            "response": chatbot.get_response(
                data['message'],
                data.get('lang', 'en')
            )
        })
        response.headers.add("Access-Control-Allow-Origin", "https://yassirham.github.io")
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/send-message", methods=["POST"])
def send_email():
    try:
        data = request.json
        msg = Message(
            subject=f"Contact: {data.get('subject')}",
            sender=data['email'],
            recipients=[os.getenv("EMAIL_USER")],
            body=f"Name: {data['name']}\nEmail: {data['email']}\nPhone: {data.get('mobile')}\n\n{data['message']}"
        )
        mail.send(msg)
        return jsonify({"message": "Email sent"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    nltk.download('punkt', download_dir='nltk_data', quiet=True)
    nltk.download('stopwords', download_dir='nltk_data', quiet=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
