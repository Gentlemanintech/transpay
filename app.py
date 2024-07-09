from flask import Flask, flash, render_template, request, session, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from helper import login_required

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///transpay.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
@login_required
def home():
    rows = db.execute("SELECT * FROM users WHERE Id = ?", session.get("user_id"))
    return render_template("home.html", rows=rows)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        firstname = request.form.get("firstName")
        lastname = request.form.get("lastName")
        phoneNumber = request.form.get("phoneNumber")
        gender = request.form.get("gender")
        email = request.form.get("email")
        password = request.form.get("password")
        passwordConfirmation = request.form.get("confirmPassword")

        if passwordConfirmation != password:
            return "Password do not match"

        name = firstname + " " + lastname
        accountNumber = "1234567890"
        amount = 10.00
        passwordHash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (name, password, email, phoneNumber, accountNumber, gender, amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       name, passwordHash, email, phoneNumber, accountNumber, gender, amount)
            return redirect("/login")
        
        except ValueError:
            return "Username already exist in our database. Go for a new one"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("email"):
            return "must provide username"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "must provide password"

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE email = ?", request.form.get("email")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            return "invalid username and/or password"

        # Remember which user has logged in
        session["user_id"] = rows[0]["Id"]

        # Redirect user to home page
        return redirect("/home")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



if __name__ == "__main__":
    app.run(debug=True)
