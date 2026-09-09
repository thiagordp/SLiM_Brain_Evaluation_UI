import os
import json

raw = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
info = json.loads(raw)

print("SERVICE ACCOUNT:", info["client_email"])