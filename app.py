import sqlite3
from flask import Flask, flash, render_template, request, session, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from helper import login_required, is_valid_email, is_valid_phone, is_strong_password, generate_account_number, naira
from datetime import datetime, timedelta

# initializing the flask app
app = Flask(__name__) 

# This tells jinja template that you want this as a custom usage/template to use. {{total | naira}} this is how it's used in html template.
app.jinja_env.filters["naira"] = naira

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///transpay.db")

# this code here sets the browser on which the user visits not to save any cache so it gets latest version of the page.
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# this is the route for my index page
@app.route("/")
def index():
    # I clear all session if there's any once index is been accessed and render the index page
    session.clear()
    return render_template("index.html")

# This is a route to the home page after the user logged in successfully.
@app.route("/home")
@login_required
def home():
    # Here I checked if the user is registered. if yes then get his details and display it on the home page.
    rows = db.execute("SELECT * FROM users WHERE Id = ?", session.get("user_id"))
    routes = db.execute("SELECT * FROM rides")
    # this line here gets me the current pin of the user.
    pin = rows[0]['pin']
    # Here I render the home page plus I passed the user details and rides available to use in the page.
    return render_template("home.html", rows=rows, pin=pin, routes=routes)

# This is my route to Registration page, where users can create their account.
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # This code checks whether the user gets to the page on POST(sending a data to the server) e.g maybe submitting a form 
    if request.method == "POST":
        # the codes get all the response a user typed on the page.
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
            return redirect("/register")
        elif not is_valid_phone(phoneNumber):
            flash('Phone number is invalid. It should be in the format 123-456-7890', 'error')
            return redirect("/register")
        elif gender not in ['Male', 'Female', 'Other']:
            flash('Gender must be Male, Female, or Other', 'error')
            return redirect("/register")
        elif not is_valid_email(email):
            flash('Email is invalid', 'error')
            return redirect("/register")
        elif not is_strong_password(password):
            flash('Password is not strong enough. It must be at least 8 characters long, contain both uppercase and lowercase letters, and at least one number', 'error')
            return redirect("/register")
        elif password != passwordConfirmation:
            flash('Passwords do not match', 'error')
            return redirect("/register")

        # All validations passed, proceed to concatenates the name so it can be stored as a single column in database.
        name = firstname + " " + lastname
        # this code below generate a random 10 digits account number.
        accountNumber = generate_account_number()
        # Here the code will hash the password to save it in db instead of the password supplied by user, even if there's access to the db, the password wont be known.
        passwordHash = generate_password_hash(password)

        # Here your account is created if it passed the constraints check on db i.e no duplicate of email of phone number.
        try:
            db.execute("INSERT INTO users (name, pass, email, phoneNumber, accountNumber, gender) VALUES (?, ?, ?, ?, ?, ?)",
                       name, passwordHash, email, phoneNumber, accountNumber, gender)
            flash("Account created succesfully")
            return redirect("/login")
        # if your account already exist it will return a message telling you
        except ValueError:
            flash("Email already exists. Choose a different one.", "error")
            return redirect("/register")
        
    # this code here will return if it's not a post method. It will render the register page.
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

        # Check database for details of the user if the email the user typed exist.
        rows = db.execute(
            "SELECT * FROM users WHERE email = ?", request.form.get("email")
        )

        # checks if email exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["pass"], request.form.get("password")
        ):
            flash("invalid email or password", "error")
            return render_template("login.html")

        # Remember which user has logged in i.e by storing the user_id in a session.
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page if logged in successfully
        return redirect("/home")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id. This will clear the session saved.
    session.clear()

    # Redirect user to index page
    return redirect("/")

# This route is the logic of user setting his pin
@app.route("/set-pin", methods=["POST"])
@login_required
def setPin():
    user_id = session.get("user_id")
    pin = request.form.get("pin")
    confirmPin = request.form.get("confirmPin")

   # if user didn't give data on any of this it will flash the message under
    if not pin or not confirmPin:
        flash("Fill both fields to set your PIN", "error")
        return redirect('/home')

    # Checks if the pin is 4 digits and it is the same as confirmPin the user typed. and det the pin in users database
    if len(pin) == 4 and pin == confirmPin:
        db.execute("UPDATE users SET pin = ? WHERE id = ?", int(pin), user_id)
        flash("Your pin has been set up successfully")
    # if it didn't match it will return a message that it's not matched
    else:
        flash("Your pin did not match", "error")

    # if the pin was set successfully it will take you back to home.
    return redirect("/home")

# This is a route where users buy airtime for their phone.
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
        # if the number the user typed is not up to 11 digits, it will return the message in flash() and redirect user to that same page
        if len(phoneNumber) != 11:
            flash("Phone number should be 11-digit number")
            return redirect("/airtime")
        
        # if the amount the user typed is less than 50NGN then it will return an error message
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
        # if the pin did not match the one in the database of the user it'll fail and return the flash message
        if int(pin) != int(confirmPin):
            flash("Your transaction pin is not correct")
            return redirect("/airtime")

        if int(amount) > int(usersCurrentCash):
            flash("You do not have sufficient fund")
            return redirect("/airtime")
        
        # if checks passed then it will update the users current balance
        db.execute("UPDATE users SET amount = amount - ? WHERE id = ?", int(amount), user_id)
        # And insert the transaction into the history db.
        db.execute("INSERT INTO transactions (user_id, price, action, date) VALUES (?, ?, ?, ?)", user_id, int(amount), action, date)
        flash("You have bought airtime successfully")
        return redirect("/home")
        
    else:
        return render_template("airtime.html")

# The code here is similar to the airtime, it shares the same logic just that the amount of data plans is fixed here.
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

# This code allows user to fund their account.
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
        
        # if the pin matched then it will update the amount in the database and add your transaction to history and take you to homepage.
        db.execute("UPDATE users SET amount = amount + ? WHERE id = ?", int(amount), user_id)
        db.execute("INSERT INTO transactions (user_id, price, action, date) VALUES (?, ?, ?, ?)", user_id, int(amount), action, date)
        flash(f"₦{amount} has been added to your wallet successfully!")
        return redirect("/home")

    else:
        return render_template("fundAccount.html")
    
# this code allows user to see all their transaction history, from adding money to account to buying a ticket you'll see the transactions all.
@app.route("/transaction-history")
@login_required
def transactionHistory():
    user_id = session.get("user_id")
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC", user_id)
    return render_template("transHistory.html", transactions=transactions)

# This code is where the logic of available routes are
@app.route("/rides", methods=["POST", "GET"])
@login_required
def rides():
    if request.method == "POST":
        search = request.form.get("search")
        if not search:
            flash("Enter something in the search bar")
            return redirect("/rides")
        # here is a variable I initiate as the user did not search for anything, but will update it to True if user did.
        searched = False
        # The query to get the rides with the stuff the user search for e.g al qalam.
        routes = db.execute("SELECT * FROM rides WHERE LOWER(fromLoc) LIKE ? or LOWER(toLoc) LIKE ?", '%'+search.lower()+'%', '%'+search.lower()+'%')
        
        # Here if the user typed in a query to search, now you see I changed the variable searched to true because the user searched. 
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
    
# This is when a user clicks on the book space and input the seat quatity.
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
    
    # If the user chose a seat quantity that is more than the seat in the ride, it will return that message in flash()
    if int(seatQty) > int(rideQty):
        flash("They're not enough seats in the Ride.")
        return redirect("/home")
    
    if not int(seatQty):
        flash("You can only type in Numbers")
        return redirect("/home")

    # if all checks are passed then the ticket is added to cart i.e saved to session so you can retrieve it easily, then take you to ticket counter page.
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

# This is the route to ticket couter. More like a cart where the user make payment for the tickets
@app.route("/ticket-bag")
@login_required
def ticketCart():
    userCart = session.get("cart", [])
    subtotal = sum(item['totalFare'] for item in userCart)
    charges = 0.0
    total = int(subtotal) + charges
    return render_template('ticketCart.html', userCart=userCart, subtotal=subtotal, charges=charges, total=total)

# This is for the cancel ticket button in the counter(cart). When a user clicks it the ticket is been taken off from the counter and return the user to homepage.
@app.route("/cancel-ticket", methods=["POST"])
@login_required
def cancelTicket():
    if 'cart' in session:
        # Get index or identifier of the item to be removed.
        rideid = request.form.get('id')
        
        # This removed item by identifier
        for cart_item in session['cart']:
            if cart_item['id'] == rideid:
                session['cart'].remove(cart_item)
                break
    
    return redirect("/home")

#This is when you clicked on the Next and pay button. This finalised your ticket.
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
                # This code checks the usersCurrent cash if it's more than the total fare and if yes it will buy the ticket
                if int(usersCurrentCash) >= int(cart_item['totalFare']):
                    db.execute("INSERT INTO tickets (user_id, fromLoc, toLoc, status, seatQty) VALUES (?, ?, ?, ?, ?)", user_id, cart_item['from'], cart_item['to'], status, cart_item['seatQty'])
                    db.execute("UPDATE users SET amount = amount - ? WHERE id = ?", int(cart_item['totalFare']), user_id)
                    db.execute("INSERT INTO transactions (user_id, price, action, date) VALUES (?, ?, ?, ?)", user_id, int(cart_item['totalFare']), action, date)
                    db.execute("UPDATE rides SET seat = seat - ? WHERE id = ?", int(cart_item['seatQty']), cart_item['rideId'])
                    session['cart'].remove(cart_item)
                    flash("Ticket bought successfully!")
                    return redirect("/ticket-page")
                else:
                    # if user has no sufficient fund it will return this message
                    flash("You do not have sufficient funds to buy this")
                    return redirect("/ticket-bag")

                
    # If the cart item is not found, show an error message
    flash("Ticket not found in cart.")
    return redirect("/ticket-bag")

# This here is the route where the ticket bought is displayed so a user can be confirmed by drivers.
@app.route("/ticket-page")
@login_required
def ticketPage():
    ticketDetails = db.execute("SELECT users.name, tickets.fromLoc, tickets.toLoc, tickets.status, tickets.date, tickets.seatQty FROM users JOIN tickets ON tickets.user_id = users.id WHERE users.id = ? AND status = 'Open' ", session.get("user_id"))
    return render_template("ticketPage.html", ticketDetails=ticketDetails)

# This code here resets the seat of the rides to their initial seat number and set a date thats an hour ahead from current time. Also closes all the tickets that are opened
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

# This is how users see all the ticket they bought
@app.route("/tickets-history")
@login_required
def ticketsHistory():
    user_id = session.get("user_id")
    # the ORDER BY DESC is setting the last transaction on top.
    tickets = db.execute("SELECT * FROM tickets WHERE user_id = ? ORDER BY date DESC", user_id)
    return render_template("ticketTrans.html", tickets=tickets)

# This is the route to users profile.
@app.route("/profile")
@login_required
def profile():
    user_id = session.get("user_id")
    profile = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    return render_template("profile.html", profile=profile)

# There's a button in the profile for change pin. This here is the logic that makes it happen
@app.route("/change-pin", methods=["POST"])
@login_required
def changePin():
    oldPin = request.form.get("oldPin")
    newPin = request.form.get("newPin")
    confirmPin = request.form.get("confirmPin")
    data = db.execute("SELECT pin FROM users WHERE id = ?", session.get("user_id"))
    userPin = data[0]['pin']

    if not oldPin or not newPin or not confirmPin:
        flash("Make sure you fill all the spaces")
        return redirect("/profile")
    
    try:
        if not int(oldPin) and not int(newPin) and not int(confirmPin):
            flash("Should be numbers only")
            return redirect('/profile')
    except ValueError:
        flash("You can only type 4 digit numbers")
        return redirect('/profile')
    
    if int(newPin) != int(confirmPin):
        flash("Your new pin is not matched")
        return redirect("/profile")
    
    if int(oldPin) != int(userPin):
        flash("Your old pin is not correct")
        return redirect("/profile")
    
    db.execute("UPDATE users SET pin = ? WHERE id = ?", newPin, session.get("user_id"))
    flash("You have updated your transaction pin successfully")
    return redirect("/profile")




if __name__ == "__main__":
    app.run(debug=True)