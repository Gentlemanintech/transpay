# Tran$pay Wallet App

## Overview

Tran$pay Wallet App is designed to facilitate cashless transactions within the university environment. It allows students and university members to perform various financial activities such as booking buses, purchasing airtime/data, managing transaction history, funding accounts, setting transaction PINs, purchasing tickets, and more.

## Features

- **Cashless Transactions:** Eliminate the need for cash transactions on campus.
- **Bus Booking:** Book buses conveniently through the app.
- **Airtime/Data Purchase:** Purchase airtime and data packages directly from the app.
- **Transaction History:** View detailed transaction history for transparency and record-keeping.
- **Account Funding:** Easily fund your wallet account through supported payment methods.
- **Transaction PIN:** Set up a secure PIN for authorizing transactions.
- **Ticket Management:** Purchase tickets and manage them within the app.
- **PIN Change:** Ability to change the transaction PIN for security reasons.
- **Logout Functionality:** Securely log out from the app to protect user accounts.

## Video Demo

Watch my video demo to see the Tran$pay Wallet App in action:

[![Tran$pay Wallet App Demo Video]](https://youtu.be/Ot2OfFsUQBE)

Description: In this video demo, you'll see how to use Tran$pay Wallet App to perform various tasks such as booking a bus, purchasing airtime, viewing transaction history, funding your account, setting up a transaction PIN, purchasing tickets, and logging out securely. 

## Security

- **Password Security:** User passwords are securely hashed before being stored in the database. This means that passwords are converted into irreversible hashes using strong cryptographic algorithms. As a result, no one, including administrators, can view or retrieve plain-text passwords from the database.
- **Database Security:** The app uses SQLite for database operations, ensuring data integrity and reliability. Access to sensitive user information is protected through secure coding practices and data encryption where applicable.


## Technologies Used

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python (Flask framework)
- **Database:** SQLite

## Installation

1. Clone the repository:
git clone https://github.com/Gentlemanintech/transpay.git

2. Navigate into the project directory:
cd project

3. Install dependencies:
pip install -r requirements.txt

4. Run the application:
flask run

5. Access the application in your web browser at `http://localhost:5000` or a specified port..

## Usage

1. **Register:** Enter your details to log into your account.
2. **Login:** Enter your credentials to access your account.
3. **Main Dashboard:** Navigate through different features like bus booking, airtime purchase, etc.
3. **Transaction History:** View your past transactions to keep track of your spending.
4. **Wallet Management:** Fund your wallet, set or change your transaction PIN, purchase tickets, etc.
5. **Logout:** Securely log out from your account after usage.


