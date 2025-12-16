import re
from typing import Dict, Tuple
from app.models import TicketCategory, TicketPriority
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
import os


class TicketClassifier:
    """Rule-based and ML-powered ticket classification"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.classifier = MultinomialNB()
        self.is_trained = False
        
        # Rule-based patterns for quick classification
        self.patterns = {
            TicketCategory.PASSWORD_RESET: [
                r'password\s+(reset|change|forgot|forgotten|expired)',
                r'(reset|change|forgot|forgotten)\s+password',
                r'can\'t\s+(login|log\s+in|sign\s+in)',
                r'locked\s+out',
                r'password\s+doesn\'t\s+work'
            ],
            TicketCategory.ACCOUNT_UNLOCK: [
                r'account\s+(locked|disabled|suspended)',
                r'unlock\s+account',
                r'(locked|disabled)\s+account',
                r'too\s+many\s+(login\s+)?attempts'
            ],
            TicketCategory.VPN_ISSUE: [
                r'vpn\s+(not\s+working|connection|issue|problem|error)',
                r'(can\'t|cannot)\s+connect\s+to\s+vpn',
                r'vpn\s+(disconnected|timeout)',
                r'remote\s+access\s+(issue|problem|not\s+working)'
            ],
            TicketCategory.ACCESS_REQUEST: [
                r'(need|request|require)\s+(access|permission)',
                r'access\s+to\s+\w+',
                r'permission\s+(denied|required)',
                r'(grant|give|provide)\s+(access|permission)',
                r'add\s+(me\s+)?to\s+group'
            ],
            TicketCategory.DEVICE_COMPLIANCE: [
                r'device\s+(compliance|not\s+compliant|out\s+of\s+date)',
                r'(security\s+)?patch(es)?\s+(needed|required|missing)',
                r'(update|updates)\s+(needed|required|available)',
                r'antivirus\s+(out\s+of\s+date|not\s+updated)',
                r'device\s+health\s+check'
            ],
            TicketCategory.EMAIL_ISSUE: [
                r'email\s+(not\s+working|issue|problem)',
                r'(can\'t|cannot)\s+(send|receive)\s+email',
                r'outlook\s+(issue|problem|not\s+working)',
                r'mailbox\s+(full|quota)'
            ]
        }
        
        # Priority keywords
        self.priority_keywords = {
            TicketPriority.CRITICAL: ['critical', 'urgent', 'emergency', 'down', 'outage', 'cannot work'],
            TicketPriority.HIGH: ['high priority', 'asap', 'important', 'blocking'],
            TicketPriority.MEDIUM: ['medium', 'normal'],
            TicketPriority.LOW: ['low priority', 'when possible', 'minor']
        }
    
    def classify_by_rules(self, text: str) -> Tuple[TicketCategory, float]:
        """Use rule-based patterns for classification"""
        text_lower = text.lower()
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    # High confidence for rule-based match
                    return category, 0.95
        
        # Default to OTHER with low confidence
        return TicketCategory.OTHER, 0.3
    
    def determine_priority(self, text: str) -> TicketPriority:
        """Determine ticket priority based on keywords"""
        text_lower = text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return priority
        
        # Default to medium priority
        return TicketPriority.MEDIUM
    
    def classify(self, subject: str, description: str) -> Dict:
        """
        Classify ticket and determine priority
        Returns: {
            'category': TicketCategory,
            'confidence': float,
            'priority': TicketPriority,
            'can_auto_resolve': bool
        }
        """
        # Combine subject and description for classification
        text = f"{subject} {description}"
        
        # Try rule-based classification first
        category, confidence = self.classify_by_rules(text)
        
        # Determine priority
        priority = self.determine_priority(text)
        
        # Determine if ticket can be auto-resolved
        # High confidence + specific categories = auto-resolvable
        can_auto_resolve = (
            confidence >= 0.8 and 
            category in [
                TicketCategory.PASSWORD_RESET,
                TicketCategory.ACCOUNT_UNLOCK,
                TicketCategory.VPN_ISSUE,
                TicketCategory.DEVICE_COMPLIANCE
            ]
        )
        
        return {
            'category': category,
            'confidence': confidence,
            'priority': priority,
            'can_auto_resolve': can_auto_resolve
        }
    
    def extract_user_from_ticket(self, subject: str, description: str, requester_email: str) -> str:
        """Extract the affected user from ticket content"""
        text = f"{subject} {description}".lower()
        
        # Look for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Filter out the requester's email
        affected_emails = [email for email in emails if email.lower() != requester_email.lower()]
        
        if affected_emails:
            return affected_emails[0]
        
        # Look for "for [username]" or "user [username]" patterns
        user_patterns = [
            r'for\s+user\s+(\w+)',
            r'user\s+(\w+)',
            r'for\s+(\w+@\w+)',
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Default to requester
        return requester_email
    
    def train_model(self, training_data: list):
        """Train the ML classifier with historical data"""
        if not training_data:
            return
        
        texts = [f"{item['subject']} {item['description']}" for item in training_data]
        labels = [item['category'] for item in training_data]
        
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        self.is_trained = True
    
    def save_model(self, path: str = "models/"):
        """Save trained model to disk"""
        os.makedirs(path, exist_ok=True)
        with open(f"{path}vectorizer.pkl", "wb") as f:
            pickle.dump(self.vectorizer, f)
        with open(f"{path}classifier.pkl", "wb") as f:
            pickle.dump(self.classifier, f)
    
    def load_model(self, path: str = "models/"):
        """Load trained model from disk"""
        try:
            with open(f"{path}vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)
            with open(f"{path}classifier.pkl", "rb") as f:
                self.classifier = pickle.load(f)
            self.is_trained = True
            return True
        except FileNotFoundError:
            return False


# Global classifier instance
ticket_classifier = TicketClassifier()
