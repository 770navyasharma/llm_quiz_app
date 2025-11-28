import matplotlib.pyplot as plt
import base64
import pandas as pd
import requests
import re
import io
import PyPDF2
import math
import numpy as np
import json
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib.parse # <--- Added this so 'urllib' is available too
import warnings

# Suppress warnings to keep logs clean
warnings.filterwarnings("ignore")

class CodeExecutor:
    def __init__(self, email, secret):
        self.email = email
        self.secret = secret

    def execute(self, code_string: str, current_url: str):
        print("   ⚙️ Executing Autonomous Script...")
        
        output_buffer = io.StringIO()
        
        # 1. Setup Browser-like Headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # 2. Define Helper function
        def safe_get(url):
            return requests.get(url, headers=headers)

        # 3. Inject Variables & Tools
        local_scope = {
            "pd": pd,
            "np": np,
            "requests": requests,
            "re": re,
            "math": math,
            "json": json,
            "PyPDF2": PyPDF2,
            "io": io,
            "BeautifulSoup": BeautifulSoup,
            
            # URL HANDLING TOOLS
            "urljoin": urljoin,           # Direct access: urljoin(base, relative)
            "urllib": urllib,             # Module access: urllib.parse.urljoin
            
            "plt": plt,
            "base64": base64,
            "print": lambda *args: output_buffer.write(" ".join(map(str, args)) + "\n"),
            "safe_get": safe_get,
            "my_email": self.email,
            "my_secret": self.secret,
            "current_url": current_url
        }
        
        try:
            # 4. Run the Code
            exec(code_string, {}, local_scope)
            
            # 5. Validate Output Variables
            if 'submission_payload' not in local_scope:
                return False, "Error: Your code finished but did not define 'submission_payload'.", output_buffer.getvalue()
            
            if 'submission_dest' not in local_scope:
                return False, "Error: Your code finished but did not define 'submission_dest' (the URL to post to).", output_buffer.getvalue()

            payload = local_scope['submission_payload']
            dest_url = local_scope['submission_dest']
            
            # 6. Sanitize Types
            payload = self.sanitize_payload(payload)
            
            return True, {"payload": payload, "dest": dest_url}, output_buffer.getvalue()
                
        except Exception:
            # Capture full traceback
            error_msg = traceback.format_exc()
            return False, f"Runtime Error:\n{error_msg}", output_buffer.getvalue()

    def sanitize_payload(self, payload):
        if isinstance(payload, dict):
            return {k: self.sanitize_payload(v) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [self.sanitize_payload(v) for v in payload]
        elif isinstance(payload, (np.integer, np.int64)):
            return int(payload)
        elif isinstance(payload, (np.floating, np.float64)):
            return float(payload)
        elif isinstance(payload, np.ndarray):
            return payload.tolist()
        return payload