from flask import Flask, flash, render_template, request, session, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from helper import login_required, is_valid_email, is_valid_phone, is_strong_password, generate_account_number, naira
from datetime import datetime, timedelta


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
    routes = db.execute("SELECT * FROM rides")
    pin = rows[0]['pin']
    return render_template("home.html", rows=rows, pin=pin, routes=routes)


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
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/set-pin", methods=["POST"])
@login_required
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

@app.route("/airtime", methods=["POST", "GET"])
@login_required
def airtime():
    if request.method == "POST":
        network = request.form.get("network")
        phoneNumber = request.form.get("phoneNumber")
        amount = request.form.get("airtimeAmount")
        pin = request.form.get("pin")

        if not network or not phoneNumber or not amount:
            flash("Make sure you fill all the field")
            return redirect("/airtime")
        
        if len(phoneNumber) != 11:
            flash("Phone number should be 11-digit number")
            return redirect("/airtime")
        
        if int(amount) < 50:
            flash("Amount should not be less than 50NGN")
            return redirect("/airtime")
        
        user_id = session.get("user_id")
        # get the users pin and cash from db.
        userPin = db.execute("SELECT pin, amount from users WHERE id = ?", user_id)
        confirmPin = userPin[0]['pin']
        usersCurrentCash = userPin[0]['amount']
        action = 'Airtime'
        date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        if not pin:
            flash("Enter your pin")
            return redirect("/airtime")
        
        if len(pin) != 4 or not int(pin):
            flash("Your transaction pin are 4-digit numbers")
            return redirect("/airtime")
        #if the pin did not match the one in the database of the user it'll fail and return the flash message
        if int(pin) != int(confirmPin):
            flash("Your transaction pin is not correct")
            return redirect("/airtime")

        if int(amount) > int(usersCurrentCash):
            flash("You do not have sufficient fund")
            return redirect("/airtime")
        
        db.execute("UPDATE users SET amount = amount - ? WHERE id = ?", int(amount), user_id)
        db.execute("INSERT INTO transactions (user_id, price, action, date) VALUES (?, ?, ?, ?)", user_id, int(amount), action, date)
        flash("You have bought airtime successfully")
        return redirect("/home")
        


    else:
        return render_template("airtime.html")


@app.route("/data", methods=["POST", "GET"])
@login_required
def data():
    if request.method == "POST":
        network = request.form.get("network")
        dataPlanAmount = request.form.get("dataPlan")
        phoneNumber = request.form.get("phoneNumber")
        pin = request.form.get("pin")

        if not network or not phoneNumber or not dataPlanAmount:
            flash("Make sure you fill all the field")
            return redirect("/data")
        
        if len(phoneNumber) != 11:
            flash("Phone number should be 11-digit number")
            return redirect("/data")

        user_id = session.get("user_id")
        # get the users pin and cash from db.
        userPin = db.execute("SELECT pin, amount from users WHERE id = ?", user_id)
        confirmPin = userPin[0]['pin']
        usersCurrentCash = userPin[0]['amount']
        action = 'Data'
        date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        if not pin:
            flash("Enter your pin")
            return redirect("/data")
        
        if len(pin) != 4 or not int(pin):
            flash("Your transaction pin are 4-digit numbers")
            return redirect("/data")
        #if the pin did not match the one in the database of the user it'll fail and return the flash message
        if int(pin) != int(confirmPin):
            flash("Your transaction pin is not correct")
            return redirect("/data")

        if int(dataPlanAmount) > int(usersCurrentCash):
            flash("You do not have sufficient fund")
            return redirect("/data")
        
        db.execute("UPDATE users SET amount = amount - ? WHERE id = ?", int(dataPlanAmount), user_id)
        db.execute("INSERT INTO transactions (user_id, price, action, date) VALUES (?, ?, ?, ?)", user_id, int(dataPlanAmount), action, date)
        flash("You have bought mobile data successfully")
        return redirect("/home")

    
    else:
        return render_template("data.html")


@app.route("/fund-account", methods=["POST", "GET"])
@login_required
def fundAccount():
    if request.method == "POST":
        amount = request.form.get("amount")
        pin = request.form.get("pin")

        # if user did not supply anything
        if not amount:
            flash("You did not specify the amount to add")
            return redirect("/fund-account")
        
        # if user sets amount less than 10NGN it will return the flash message
        if int(amount) < 10:
            flash("Enter amount not less 10 NGN")
            return redirect("/fund-account")
        
        user_id = session.get("user_id")
        # get the users pin from db.
        userPin = db.execute("SELECT pin from users WHERE id = ?", user_id)
        confirmPin = userPin[0]['pin']
        action = 'Fund account'
        date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        
        # if user did not supply pin it will flash the message
        if not pin:
            flash("Enter your pin")
            return redirect("/fund-account")
        
        if len(pin) != 4 or not int(pin):
            flash("Your transaction pin are 4-digit numbers")
            return redirect("/fund-account")
        #if the pin did not match the one in the database of the user it'll fail and return the flash message
        if int(pin) != int(confirmPin):
            flash("Your transaction pin is not correct")
            return redirect("/fund-account")
        
        # if the pin matched then it will update the amount in the database and take you to homepage.
        db.execute("UPDATE users SET amount = amount + ? WHERE id = ?", int(amount), user_id)
        db.execute("INSERT INTO transactions (user_id, price, action, date) VALUES (?, ?, ?, ?)", user_id, int(amount), action, date)
        flash(f"₦{amount} has been added to your wallet successfully!")
        return redirect("/home")

    else:
        return render_template("fundAccount.html")
    

@app.route("/transaction-history")
@login_required
def transactionHistory():
    user_id = session.get("user_id")
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC", user_id)
    return render_template("transHistory.html", transactions=transactions)


@app.route("/rides", methods=["POST", "GET"])
@login_required
def rides():
    if request.method == "POST":
        search = request.form.get("search")
        if not search:
            flash("Enter something in the search bar")
            return redirect("/rides")
        
        searched = False
        routes = db.execute("SELECT * FROM rides WHERE LOWER(fromLoc) LIKE ? or LOWER(toLoc) LIKE ?", '%'+search.lower()+'%', '%'+search.lower()+'%')
        
        if routes:
            searched = True
            return render_template("rides.html", routes=routes, searched=searched, search=search)
        elif not routes:
            flash("No such route available")
            return redirect("/rides")
        else:
            return redirect("/rides")
        
    else:
        routes = db.execute("SELECT * FROM rides")
        return render_template("rides.html", routes=routes)
    

@app.route("/ticket", methods=["POST"])
@login_required
def ticketBuy():
    if "cart" not in session:
        session["cart"] = []


    id = request.form.get("id")
    seatQty = request.form.get("seatQty")
    rideDetails = db.execute("SELECT * FROM rides WHERE id = ?", id)
    rideQty = rideDetails[0]['seat']
    rideName = rideDetails[0]['name']
    time = rideDetails[0]['time']
    date = rideDetails[0]['date']
    fromLoc = rideDetails[0]['fromLoc']
    toLoc = rideDetails[0]['toLoc']
    tfare = rideDetails[0]['fare']
    totalFare = rideDetails[0]['fare'] * int(seatQty)
    rideNumber = rideDetails[0]['rideNumber']
    rideId = rideDetails[0]['id']
    date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    if int(seatQty) > int(rideQty):
        flash("They're not enough seats in the Ride.")
        return redirect("/home")
    
    if not int(seatQty):
        flash("You can only type in Numbers")
        return redirect("/home")

    session["cart"].append({
        "id": date,
        "rideName": rideName,
        "rideNumber": rideNumber,
        "time": time,
        "date": date,
        "from": fromLoc,
        "to": toLoc,
        "seatQty": seatQty,
        "tfare": tfare,
        "totalFare": totalFare,
        "rideId": rideId
    })
    return redirect("/ticket-bag")


@app.route("/ticket-bag")
@login_required
def ticketCart():
    userCart = session.get("cart", [])
    subtotal = sum(item['totalFare'] for item in userCart)
    charges = 0.0
    total = int(subtotal) + charges
    return render_template('ticketCart.html', userCart=userCart, subtotal=subtotal, charges=charges, total=total)


@app.route("/cancel-ticket", methods=["POST"])
@login_required
def cancelTicket():
    if 'cart' in session:
        # Get index or identifier of the item to be removed (you'll typically pass this via POST request)
        rideid = request.form.get('id')
        
        # Example of removing item by identifier (adjust based on how your data is structured)
        for cart_item in session['cart']:
            if cart_item['id'] == rideid:
                session['cart'].remove(cart_item)
                break
    
    return redirect("/home")


@app.route("/pay-ticket", methods=["POST"])
@login_required
def payTicket():
    pin = request.form.get("pin")
    id = request.form.get("id")
    status = 'Open'
    action = 'Ticket'
    user_id = session.get("user_id")
    userDetails = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    usersCurrentCash = userDetails[0]['amount']
    confirmPin = userDetails[0]['pin']
    date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    if not pin:
            flash("Enter your pin")
            return redirect("/ticket-bag")
    try:
        if len(pin) != 4 or not int(pin):
            flash("Your transaction pin are 4-digit numbers")
            return redirect("/ticket-bag")
    except ValueError:
        flash("Your transaction pin should be 4-digit numbers")
        return redirect("/ticket-bag")
        #if the pin did not match the one in the database of the user it'll fail and return the flash message
    if int(pin) != int(confirmPin):
            flash("Your transaction pin is not correct")
            return redirect("/ticket-bag")    

    # Check if 'cart' exists in session and is not empty
    if 'cart' in session and session['cart']:
        for cart_item in session['cart']:
            if cart_item['id'] == id:
                if int(usersCurrentCash) >= int(cart_item['totalFare']):
                    db.execute("INSERT INTO tickets (user_id, fromLoc, toLoc, status, seatQty) VALUES (?, ?, ?, ?, ?)", user_id, cart_item['from'], cart_item['to'], status, cart_item['seatQty'])
                    db.execute("UPDATE users SET amount = amount - ? WHERE id = ?", int(cart_item['totalFare']), user_id)
                    db.execute("INSERT INTO transactions (user_id, price, action, date) VALUES (?, ?, ?, ?)", user_id, int(cart_item['totalFare']), action, date)
                    db.execute("UPDATE rides SET seat = seat - ? WHERE id = ?", int(cart_item['seatQty']), cart_item['rideId'])
                    session['cart'].remove(cart_item)
                    flash("Ticket bought successfully!")
                    return redirect("/ticket-page")
                else:
                    flash("You do not have sufficient funds to buy this")
                    return redirect("/ticket-bag")

                
    # If the cart item is not found, show an error message
    flash("Ticket not found in cart.")
    return redirect("/ticket-bag")


@app.route("/ticket-page")
@login_required
def ticketPage():
    ticketDetails = db.execute("SELECT users.name, tickets.fromLoc, tickets.toLoc, tickets.status, tickets.date, tickets.seatQty FROM users JOIN tickets ON tickets.user_id = users.id WHERE users.id = ? AND status = 'Open' ", session.get("user_id"))
    return render_template("ticketPage.html", ticketDetails=ticketDetails)


@app.route("/reset", methods=["POST"])
@login_required
def reset():
    user_id = session.get("user_id")
    date = datetime.now()
    currDate = date.strftime("%m/%d/%Y")
    currTime = date + timedelta(hours=1)
    time = currTime.strftime("%H:%M:%S")

    db.execute("UPDATE tickets SET status = 'Close' WHERE user_id = ?", user_id)
    db.execute("UPDATE rides SET seat = 33, date = ?, time = ? WHERE id = 1", currDate, time)
    db.execute("UPDATE rides SET seat = 3, date = ?, time = ? WHERE id = 2", date, time)
    
    return redirect("/home")

@app.route("/tickets-history")
@login_required
def ticketsHistory():
    user_id = session.get("user_id")
    tickets = db.execute("SELECT * FROM tickets WHERE user_id = ? ORDER BY date DESC", user_id)
    return render_template("ticketTrans.html", tickets=tickets)


if __name__ == "__main__":
    app.run(debug=True)