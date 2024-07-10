from flask import Flask, flash, render_template, request, session, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from helper import login_required, is_valid_email, is_valid_phone, is_strong_password, generate_account_number, naira


app = Flask(__name__)

app.jinja_env.filters["naira"] = naira

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
    session.clear()
    return render_template("index.html")

@app.route("/home")
@login_required
def home():
    rows = db.execute("SELECT * FROM users WHERE Id = ?", session.get("user_id"))
    pin = rows[0]['pin']
    return render_template("home.html", rows=rows, pin=pin)


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

        # Validation checks
        if not firstname or not lastname:
            flash('First name and last name are required', 'error')
            return render_template("register.html")
        elif not is_valid_phone(phoneNumber):
            flash('Phone number is invalid. It should be in the format 123-456-7890', 'error')
            return render_template("register.html")
        elif gender not in ['Male', 'Female', 'Other']:
            flash('Gender must be Male, Female, or Other', 'error')
            return render_template("register.html")
        elif not is_valid_email(email):
            flash('Email is invalid', 'error')
            return render_template("register.html")
        elif not is_strong_password(password):
            flash('Password is not strong enough. It must be at least 8 characters long, contain both uppercase and lowercase letters, and at least one number', 'error')
            return render_template("register.html")
        elif password != passwordConfirmation:
            flash('Passwords do not match', 'error')
            return render_template("register.html")

        # All validations passed, proceed with insertion
        name = firstname + " " + lastname
        # this code below generate a random 10 digits account number.
        accountNumber = generate_account_number()
        # Here the code will hash the password to save it in db instead of the password supplied by user.
        passwordHash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (name, pass, email, phoneNumber, accountNumber, gender) VALUES (?, ?, ?, ?, ?, ?)",
                       name, passwordHash, email, phoneNumber, accountNumber, gender)
            flash("Account created succesfully")
            return redirect("/register")
        except ValueError:
            flash("Email already exists. Choose a different one.", "error")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure email was submitted
        if not request.form.get("email"):
            flash("must provide email", "error")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password", "error")
            return render_template("login.html")

        # Query database for email
        rows = db.execute(
            "SELECT * FROM users WHERE email = ?", request.form.get("email")
        )

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["pass"], request.form.get("password")
        ):
            flash("invalid email or password", "error")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/home")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/set-pin", methods=["POST"])
def setPin():
    user_id = session.get("user_id")
    pin = request.form.get("pin")
    confirmPin = request.form.get("confirmPin")

    if not pin or not confirmPin:
        flash("Fill both fields to set your PIN", "error")
        return redirect('/home')

    if len(pin) == 4 and pin == confirmPin:
        db.execute("UPDATE users SET pin = ? WHERE id = ?", int(pin), user_id)
        flash("Your pin has been set up successfully")
    else:
        flash("Your pin did not match", "error")

    return redirect("/home")

@app.route("/airtime")
def airtime():
    return render_template("airtime.html")


@app.route("/data")
def data():
    return render_template("data.html")



if __name__ == "__main__":
    app.run(debug=True)
