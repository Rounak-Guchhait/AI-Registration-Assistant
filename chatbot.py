"""
AI Registration Assistant - Chatbot
Free Online AI & Data Science Internship Task AI-SS-001
Domain: Student Support & Internship Management
Description: An intelligent chatbot that guides students through
the internship registration process using NLP and Conversational AI.
"""

import json
import os
import random
import re
from datetime import datetime

from storage import load_registrations, save_registration

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# Machine Learning components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# -------------------------------------------------------------------
# 1. NLTK DATA SETUP
# -------------------------------------------------------------------
# Download the required NLTK resources on first run.
# Each resource lives in a specific sub-folder:
#   punkt / punkt_tab  -> tokenizers/
#   stopwords          -> corpora/
#   wordnet            -> corpora/
NLTK_RESOURCES = {
    'punkt': 'tokenizers/punkt',
    'punkt_tab': 'tokenizers/punkt_tab',
    'stopwords': 'corpora/stopwords',
    'wordnet': 'corpora/wordnet',
}


def _ensure_nltk_data():
    helper = nltk.downloader.Downloader()  # manual downloader for reliable extraction
    for resource in NLTK_RESOURCES:
        try:
            nltk.data.find(NLTK_RESOURCES[resource])
        except LookupError:
            helper.download(resource, quiet=True)


_ensure_nltk_data()


class RegistrationAssistant:
    """
    Main chatbot class.
    Handles: preprocessing, intent classification, entity extraction,
    dialog management, validation, and response generation.
    """

    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

        # Paths for data files
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.intents_file = os.path.join(self.base_dir, 'intents.json')
        self.registrations_file = os.path.join(self.base_dir, 'registrations.json')

        self.intents = self.load_intents()

        # Conversation state
        self.user_data = {}
        self.state = 'IDLE'  # IDLE, AWAITING_NAME, AWAITING_EMAIL, AWAITING_FIELD, AWAITING_EXPERIENCE, CONFIRMATION

        # ML model (trained from intent patterns)
        self.model = None
        self.vectorizer = None
        self.train_intent_model()

        # Badge definitions for sentiment (bonus feature)
        self.positive_words = {'good', 'great', 'nice', 'awesome', 'thanks', 'thank', 'happy', 'love', 'cool', 'perfect'}

    # -------------------------------------------------------------------
    # FILE LOADING
    # -------------------------------------------------------------------
    def load_intents(self):
        """Load intent patterns and responses from intents.json."""
        with open(self.intents_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert list-of-dicts format to dict format for convenience
        intents = {}
        for item in data['intents']:
            intents[item['tag']] = {
                'patterns': item['patterns'],
                'responses': item['responses']
            }
        return intents

    # -------------------------------------------------------------------
    # 2. MACHINE LEARNING: INTENT CLASSIFIER TRAINING
    # -------------------------------------------------------------------
    def train_intent_model(self):
        """
        Train a Naive Bayes classifier on the intent patterns using
        TF-IDF vectorization. This gives the chatbot an ML-based
        understanding of user input (beyond simple keyword matching).
        """
        X_texts = []
        y_labels = []

        for tag, data in self.intents.items():
            for pattern in data['patterns']:
                X_texts.append(pattern)
                y_labels.append(tag)

        # Build a pipeline: TF-IDF -> Multinomial Naive Bayes
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(tokenizer=self._tokenize)),
            ('clf', MultinomialNB())
        ])
        self.model.fit(X_texts, y_labels)

    def _tokenize(self, text):
        """Tokenizer used by the vectorizer (returns cleaned tokens)."""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        return nltk.word_tokenize(text)

    # -------------------------------------------------------------------
    # 3. TEXT PREPROCESSING
    # -------------------------------------------------------------------
    def preprocess_text(self, text):
        """
        Clean and preprocess user input:
        lowercase -> remove punctuation -> tokenize -> remove stopwords -> lemmatize
        """
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        tokens = nltk.word_tokenize(text)
        tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words
        ]
        return tokens

    # -------------------------------------------------------------------
    # 4. INTENT CLASSIFICATION
    # -------------------------------------------------------------------
    def classify_intent_ml(self, text):
        """
        Classify intent using the trained ML model, but only if confidence
        is reasonably high. Returns 'unknown' when uncertain so the
        rule-based classifier can take over.
        """
        try:
            proba = self.model.predict_proba([text])[0]
            best_idx = int(proba.argmax())
            best_conf = float(proba[best_idx])
            # Confidence threshold: require a clear majority
            if best_conf >= 0.45:
                return self.model.classes_[best_idx]
            return 'unknown'
        except Exception:
            return 'unknown'

    def classify_intent_rules(self, text):
        """Rule-based keyword fallback classification.

        Specific intents are checked first (longer/more specific patterns),
        then generic ones. This handles topics like internship info and
        required skills that keyword matching alone can detect reliably.
        """
        text_lower = text.lower()

        # Pass-through for exact-question helpers
        if any(p in text_lower for p in self.intents['internship_details']['patterns']):
            return 'internship_details'
        if any(p in text_lower for p in self.intents['skills']['patterns']):
            return 'skills'
        if any(p in text_lower for p in self.intents['help']['patterns']):
            return 'help'

        # Generic keyword scan over remaining intents
        for intent, data in self.intents.items():
            for pattern in data['patterns']:
                if pattern in text_lower:
                    return intent
        return 'unknown'

    def classify_intent(self, text):
        """
        Combine both approaches:
        1. Rule-based first (reliable, targeted topic detection)
        2. ML model as a general fallback when rules find nothing
        """
        rule_intent = self.classify_intent_rules(text)
        if rule_intent != 'unknown':
            return rule_intent
        ml_intent = self.classify_intent_ml(text)
        if ml_intent != 'unknown':
            return ml_intent
        return 'unknown'

    # -------------------------------------------------------------------
    # 5. ENTITY EXTRACTION
    # -------------------------------------------------------------------
    def extract_entities(self, text):
        """
        Extract structured information (name, email, etc.) from free text
        using regular expressions.
        """
        entities = {}

        # Name extraction: "my name is X", "i am X", "i'm X", "call me X"
        name_match = re.search(
            r'(?:my name is|i am|i\'m|call me)\s+([a-zA-Z\s]+)', text, re.IGNORECASE
        )
        if name_match:
            name = name_match.group(1).strip()
            if name:
                entities['name'] = ' '.join(name.split())

        # Email extraction
        email_match = re.search(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text
        )
        if email_match:
            entities['email'] = email_match.group()

        # Field of study: "I study X", "I'm studying X", "My field is X"
        field_match = re.search(
            r'(?:i study|i\'m studying|my field is|studying|field of study is)\s+([a-zA-Z\s]+)',
            text, re.IGNORECASE
        )
        if field_match:
            field = field_match.group(1).strip()
            if field:
                entities['field'] = ' '.join(field.split())

        # Experience level
        exp_keywords = {'beginner': 'Beginner', 'intermediate': 'Intermediate',
                        'advanced': 'Advanced', 'expert': 'Expert', 'novice': 'Beginner'}
        for key, val in exp_keywords.items():
            if key in text.lower():
                entities['experience'] = val
                break

        return entities

    # -------------------------------------------------------------------
    # 6. VALIDATION
    # -------------------------------------------------------------------
    def validate_email(self, email):
        """Return True if email matches the standard pattern."""
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email.strip()))

    # -------------------------------------------------------------------
    # 7. SENTIMENT ANALYSIS (BONUS FEATURE)
    # -------------------------------------------------------------------
    def analyze_sentiment(self, text):
        """Simple positive/negative sentiment detection."""
        tokens = set(self.preprocess_text(text))
        positive = tokens.intersection(self.positive_words)
        if positive:
            return 'positive'
        negative = {'bad', 'not', 'cant', 'cannot', 'sorry', 'hate', 'wrong'}
        if tokens.intersection(negative):
            return 'negative'
        return 'neutral'

    # -------------------------------------------------------------------
    # 8. DIALOG MANAGEMENT
    # -------------------------------------------------------------------
    def handle_message(self, text):
        """
        Core conversation handler. Decides what to do based on the current
        state and the extracted intents/entities.
        Returns the assistant's reply text.
        """
        text = text.strip()
        sentiment = self.analyze_sentiment(text)
        entities = self.extract_entities(text)
        intent = self.classify_intent(text)

        # ---------- Explicit mode changes ----------
        if self.state == 'IDLE':
            if intent == 'bye':
                self.state = 'IDLE'
                return self.get_response('bye')
            if intent in ('greeting', 'help', 'thank_you'):
                return self.get_response(intent)
            if intent == 'register':
                self.state = 'AWAITING_NAME'
                return self.get_response('register')
            if intent in ('internship_details', 'skills'):
                return self.get_response(intent)
            return self.get_response('help')

        # ---------- Registration flow ----------
        if self.state == 'AWAITING_NAME':
            return self._handle_name(text, entities)

        if self.state == 'AWAITING_EMAIL':
            return self._handle_email(text, entities)

        if self.state == 'AWAITING_FIELD':
            return self._handle_field(text, entities)

        if self.state == 'AWAITING_EXPERIENCE':
            return self._handle_experience(text, entities)

        if self.state == 'CONFIRMATION':
            if intent in ('confirm_yes',):
                self._save_registration()
                self.state = 'IDLE'
                return self._confirmation_reply()
            if intent in ('confirm_no',):
                self.reset_conversation()
                self.state = 'AWAITING_NAME'
                return self.get_response('confirm_no')

        # Fallback
        return "I'm not sure I understood. Could you please rephrase?"

    def _handle_name(self, text, entities):
        name = self._guess_name(text, entities.get('name'))
        if not name:
            return "I didn't catch your name. Please tell me your full name."
        self.user_data['name'] = name
        self.state = 'AWAITING_EMAIL'
        response = self.get_response('name')
        try:
            return response.format(name=name)
        except (KeyError, IndexError):
            return response

    def _handle_email(self, text, entities):
        email = entities.get('email')
        if not email:
            # Maybe user typed email without a capture phrase - look for any email
            email = self._find_email(text)
        if not email:
            return "I need a valid email address. Please provide it (e.g., name@example.com)."
        if not self.validate_email(email):
            return "That doesn't look like a valid email. Please try again (e.g., name@example.com)."
        self.user_data['email'] = email
        self.state = 'AWAITING_FIELD'
        response = self.get_response('email')
        try:
            return response.format(email=email)
        except (KeyError, IndexError):
            return response

    def _handle_field(self, text, entities):
        field = entities.get('field')
        if not field:
            field = self._guess_field(text)
        if not field:
            return "Please tell me your field of study (e.g., Computer Science)."
        self.user_data['field'] = field
        self.state = 'AWAITING_EXPERIENCE'
        response = self.get_response('field')
        try:
            return response.format(field=field)
        except (KeyError, IndexError):
            return response

    def _handle_experience(self, text, entities):
        experience = entities.get('experience')
        if not experience:
            experience = self._guess_experience(text)
        if not experience:
            return "Please tell me your programming experience (Beginner, Intermediate, Advanced, or Expert)."
        self.user_data['experience'] = experience
        self.state = 'CONFIRMATION'
        response = self.get_response('experience')
        try:
            return response.format(experience=experience)
        except (KeyError, IndexError):
            return response

    # -------------------------------------------------------------------
    # 9. HELPERS FOR EXTRACTION / GUESSING
    # -------------------------------------------------------------------
    def _find_email(self, text):
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group() if match else None

    def _guess_name(self, text, extracted):
        if extracted:
            return extracted
        # If user just typed a single/word-ish phrase not matching patterns,
        # treat clean words (ignoring intent keywords) as the name.
        cleaned = self.preprocess_text(text)
        if cleaned:
            return ' '.join(cleaned).title()
        return None

    # Canonical fields and their known aliases (abbreviations, synonyms).
    FIELD_ALIASES = {
        'computer science': 'Computer Science',
        'cs': 'Computer Science',
        'comp sci': 'Computer Science',
        'computers': 'Computer Science',
        'information technology': 'Information Technology',
        'it': 'Information Technology',
        'i.t': 'Information Technology',
        'i.t.': 'Information Technology',
        'data science': 'Data Science',
        'ds': 'Data Science',
        'engineering': 'Engineering',
        'engg': 'Engineering',
        'statistics': 'Statistics',
        'stats': 'Statistics',
        'mathematics': 'Mathematics',
        'math': 'Mathematics',
        'maths': 'Mathematics',
        'physics': 'Physics',
        'business': 'Business',
        'bcom': 'Business',
        'b.com': 'Business',
        'management': 'Management',
        'bca': 'BCA',
        'computer applications': 'BCA',
        'bba': 'BBA',
        'btech': 'B.Tech',
        'b.tech': 'B.Tech',
    }

    def _guess_field(self, text):
        """Map the user's answer to a canonical field name using an alias map.

        Handles abbreviations and synonyms ("IT" -> Information Technology),
        as well as full phrases. Always returns a cleaned canonical value.
        """
        low = text.lower().strip()
        low = re.sub(r'\s+', ' ', low)

        # 1. Try exact / substring match against known fields and aliases.
        #    Longer aliases first so "information technology" wins over "it".
        for alias in sorted(self.FIELD_ALIASES, key=len, reverse=True):
            if alias in low:
                return self.FIELD_ALIASES[alias]

        # 2. Look for "i study / studying / my field is" phrases.
        field_phrase = re.search(
            r'(?:i study|i\'m studying|studying|my field is|field of study is)\s+([a-zA-Z.\s]+)',
            low
        )
        if field_phrase:
            phrase = field_phrase.group(1).strip()
            if phrase:
                return self._title_case(phrase)

        # 3. Fallback: return the words the user typed (cleaned up).
        words = re.findall(r'[a-zA-Z]{2,}', low)
        if len(words) >= 1:
            return ' '.join(w.title() for w in words)
        return None

    @staticmethod
    def _title_case(phrase):
        """Convert 'information technology' -> 'Information Technology'."""
        return ' '.join(w.title() for w in phrase.split())

    def _guess_experience(self, text):
        low = text.lower()
        if any(w in low for w in ['beginner', 'novice', 'none', 'no experience', 'basic', 'starting', 'new', 'fresher']):
            return 'Beginner'
        if 'intermediate' in low or 'mid' in low or 'medium' in low:
            return 'Intermediate'
        if any(w in low for w in ['advanced', 'expert', 'pro', 'experienced', 'senior']):
            return 'Advanced'
        return None

    # -------------------------------------------------------------------
    # 10. RESPONSE GENERATION
    # -------------------------------------------------------------------
    def get_response(self, intent):
        """Return a random response for the given intent."""
        if intent in self.intents:
            return random.choice(self.intents[intent]['responses'])
        return "I'm not sure I understood. Could you please rephrase your question?"

    # -------------------------------------------------------------------
    # 11. REGISTRATION SAVING & CONFIRMATION
    # -------------------------------------------------------------------
    def _save_registration(self):
        """Persist the current user data (to Postgres if available, else JSON)."""
        record = dict(self.user_data)
        record['registered_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_registration(record)

    def _confirmation_reply(self):
        return (
            "Registration confirmed! Here's your summary:\n"
            f"  Name: {self.user_data.get('name')}\n"
            f"  Email: {self.user_data.get('email')}\n"
            f"  Field of Study: {self.user_data.get('field')}\n"
            f"  Experience: {self.user_data.get('experience')}\n"
            f"Welcome to the Free Online AI & Data Science Internship!"
        )

    def reset_conversation(self):
        """Reset user data and state for a fresh registration."""
        self.user_data = {}
        self.state = 'IDLE'

    # -------------------------------------------------------------------
    # 12. INTERACTIVE CHAT LOOP
    # -------------------------------------------------------------------
    def chat(self):
        """Run the interactive command-line chat loop."""
        print("\n" + "=" * 60)
        print("  AI REGISTRATION ASSISTANT")
        print("  Free Online AI & Data Science Internship - Data Alcott Systems")
        print("  Type 'help' for options, 'bye' to exit")
        print("=" * 60)
        print("\nWelcome! I can help you with internship registration.")
        print("Say 'register' to begin, or ask me a question.\n")

        while True:
            try:
                user_input = input("You: ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input.strip():
                continue

            # Exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("Assistant: " + self.get_response('bye'))
                break

            # Admin command to view saved registrations
            if user_input.lower() == '/list':
                print("\nSaved registrations:")
                self._print_registrations()
                continue

            response = self.handle_message(user_input)
            print(f"Assistant: {response}")
            print()

    def _print_registrations(self):
        data = load_registrations()
        if not data:
            print("  (none yet)")
            return
        for i, rec in enumerate(data, 1):
            print(f"  {i}. {rec.get('name', '?')} - {rec.get('email', '?')} "
                  f"({rec.get('field', '?')} / {rec.get('experience', '?')})")


# -------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------
if __name__ == '__main__':
    assistant = RegistrationAssistant()
    # Quick validation for the demo comment below
    assistant.chat()
