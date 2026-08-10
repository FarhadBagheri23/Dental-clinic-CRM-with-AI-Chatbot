import os

# Settings are read at import time, so the environment must be set first.
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("SESSION_SECRET", "0" * 64)
