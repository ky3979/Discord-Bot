"""Firebase extension initialization and queries"""
import ast
import firebase_admin
from firebase_admin import credentials, firestore
from services.config import config

class FirebaseHandler():
    """Class to provide an instance of Firebase on the connection property"""

    def __init__(self):
        """Constuctor"""
        try:
            cred = credentials.Certificate(config.FIREBASE_CREDENTIALS)
        except Exception:
            cred = credentials.Certificate(ast.literal_eval(config.FIREBASE_CREDENTIALS))
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def query_firestore(self, collection, document=None):
        """Return a stream of the documents or the document reference itself"""
        if document is None:
            return self.db.collection(collection).stream()
        return self.db.collection(collection).document(document)
