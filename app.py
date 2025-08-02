from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Product, Bill

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Login
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

# Register (optional for testing)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'])
        new_user = User(username=request.form['username'], password=hashed_pw, role=request.form['role'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))
    if session['role'] == 'admin':
        return render_template('dashboard_admin.html')
    else:
        return render_template('dashboard_cashier.html')

# Inventory View (Admin only)
@app.route('/inventory')
def inventory():
    if session.get('role') != 'admin':
        return "Access Denied"
    products = Product.query.all()
    return render_template('inventory.html', products=products)

# Add Product (Admin only)
@app.route('/add-product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        return "Access Denied"
    name = request.form['name']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    db.session.add(Product(name=name, quantity=quantity, price=price))
    db.session.commit()
    return redirect(url_for('inventory'))

# Update Product
@app.route('/update-product/<int:id>', methods=['GET', 'POST'])
def update_product(id):
    if session.get('role') != 'admin':
        return "Access Denied"
    product = Product.query.get(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.quantity = int(request.form['quantity'])
        product.price = float(request.form['price'])
        db.session.commit()
        return redirect(url_for('inventory'))
    return render_template('update_product.html', product=product)

# Delete Product
@app.route('/delete-product/<int:id>')
def delete_product(id):
    if session.get('role') != 'admin':
        return "Access Denied"
    product = Product.query.get(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('inventory'))

# Billing (Cashier only)
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if session.get('role') != 'cashier':
        return "Access Denied"
    products = Product.query.all()
    total = 0
    purchased = []
    if request.method == 'POST':
        for product in products:
            qty = int(request.form.get(f'qty_{product.id}', 0))
            if qty > 0 and qty <= product.quantity:
                product.quantity -= qty
                total += qty * product.price
                purchased.append({'name': product.name, 'qty': qty, 'price': product.price})
        db.session.add(Bill(date=datetime.now(), total_amount=total))
        db.session.commit()
        return render_template('bill_summary.html', items=purchased, total=total)
    return render_template('billing.html', products=products)


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
