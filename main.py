from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib

app = Flask(__name__)

# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Root123'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)


# http://localhost:5000/pythonlogin/ - the following will be our login page, which will use both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Retrieve the hashed password
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return the result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg=msg)


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))



# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'^[a-z0-9_.+-]+@[gmail]+\.[com]+$', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for logged in users
# Fetch the first 10 products from the database
@app.route('/pythonlogin/home')
def home():
    if 'loggedin' in session:
        # Connect to the MySQL database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM products LIMIT 10')
        products = cursor.fetchall()

        return render_template('home.html', username=session['username'], products=products)
    return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for logged in users
@app.route('/pythonlogin/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))


@app.route('/pythonlogin/cart')
def cart():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT products.product_name, products.price, carts.quantity FROM carts JOIN products ON carts.product_id = products.product_id WHERE carts.id = %s', (user_id,))
        cart_items = cursor.fetchall()
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

        if cart_items:
            return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)
        else:
            return render_template('cart.html', no_items=True)

    # User is not logged in, redirect to login page
    return redirect(url_for('login'))


# Add this route to handle adding items to the cart
@app.route('/pythonlogin/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'loggedin' in session:
        if request.method == 'POST':
            # Get the user's ID from the session
            user_id = session['id']
            # Get the quantity selected by the user from the form
            quantity = int(request.form.get('quantity'))

            # Insert the item into the cart
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO carts (id, product_id, quantity) VALUES (%s, %s, %s)',
                           (user_id, product_id, quantity))
            mysql.connection.commit()
            cursor.close()

    return redirect(url_for('home'))

@app.route('/pythonlogin/checkout')
def checkout():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT products.product_name, products.price, carts.quantity FROM carts JOIN products ON carts.product_id = products.product_id WHERE carts.id = %s', (user_id,))
        cart_items = cursor.fetchall()
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

        if cart_items:
            cursor.execute('DELETE FROM carts WHERE id = %s', (user_id,))
            mysql.connection.commit()
            return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)
        else:
            return render_template('checkout.html', no_items=True)

    # User is not logged in, redirect to login page
    return redirect(url_for('login'))



if __name__ == "__main__":
    app.run(debug=True)