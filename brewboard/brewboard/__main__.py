import os

from .app import serve

serve(int(os.environ.get("PORT", 8766)))
