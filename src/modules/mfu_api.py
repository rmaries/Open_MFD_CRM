import requests
import os
from dotenv import load_dotenv

load_dotenv()

class MFUApi:
    def __init__(self):
        self.base_url = os.getenv("MFU_API_URL")
        self.api_key = os.getenv("MFU_API_KEY")

    def submit_order(self, payload):
        """Submit an order to MFU."""
        # API logic to be implemented
        pass

    def check_kyc_status(self, pan):
        """Check KYC status via MFU."""
        # API logic to be implemented
        pass
