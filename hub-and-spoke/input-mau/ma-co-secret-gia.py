import re
SECRET_KEY = "DEMO_ONLY_NOT_REAL"
def validate_email(email):
 return re.fullmatch(r"[^@\s]+@[^@.\s]+(?:\.[^@.\s]+)+", email.strip()) is not None
