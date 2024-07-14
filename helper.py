from flask import redirect, render_template, request, session
from functools import wraps
import re
import random


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

def is_valid_phone(phoneNumber):
    # Updated regex to match exactly 10 digits
    regex = r'^\d{10}$'
    return re.match(regex, phoneNumber) is not None

def is_strong_password(password):
    # A strong password has at least 8 characters, contains both uppercase and lowercase letters, and has at least one number
    regex = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
    return re.match(regex, password) is not None


def generate_account_number():
    # Generate a 10-digit random number
    account_number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    return account_number

# This code is sets the naira sign on html template and the .00 decimal instead of return more than 2place decimal
def naira(value):
    """Format value as Naira."""
    return f"₦{value:,.2f}"