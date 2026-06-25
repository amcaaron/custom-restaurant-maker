import os
import sqlite3
import json
import base64
import uuid
import cloudinary
import cloudinary.uploader
import stripe
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify

load_dotenv()

app = Flask(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

basedir = os.path.abspath(os.path.dirname(__file__))

database_url = os.getenv("DATABASE_URL")

if not database_url:
    database_url = "sqlite:///" + os.path.join(basedir, "project4.db")

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Customer(db.Model):
    __tablename__ = "customers"

    customer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    street_address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    phone_number = db.Column(db.String(30))
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.Text)
    created_at = db.Column(db.String(50))


class Menu(db.Model):
    __tablename__ = "menu"

    menu_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    image_url = db.Column(db.Text)


class Order(db.Model):
    __tablename__ = "orders"

    order_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.customer_id"))
    order_number = db.Column(db.String(100), unique=True, nullable=False)
    date_time = db.Column(db.String(50))
    status = db.Column(db.String(50))
    payment_method = db.Column(db.String(50))
    total_amount = db.Column(db.Float)
    stripe_session_id = db.Column(db.String(255))
    stripe_payment_status = db.Column(db.String(100))


class OrderItem(db.Model):
    __tablename__ = "order_items"

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(100), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey("menu.menu_id"))
    quantity = db.Column(db.Integer, nullable=False)


class Restaurant(db.Model):
    __tablename__ = "restaurants"

    restaurant_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    logo_filename = db.Column(db.String(255))
    logo_url = db.Column(db.Text)
    theme_color = db.Column(db.String(20))
    created_at = db.Column(db.String(50))

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect("project4.db")
    conn.row_factory = sqlite3.Row
    return conn

def upload_image_to_cloudinary(image_file, folder_name="restaurant_maker"):
    if not image_file or image_file.filename == "":
        return None

    if not allowed_file(image_file.filename):
        return None

    try:
        upload_result = cloudinary.uploader.upload(
            image_file,
            folder=folder_name,
            resource_type="image"
        )

        return upload_result.get("secure_url")

    except Exception as e:
        print("Cloudinary upload failed:", e)
        return None

def get_restaurant():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM restaurants LIMIT 1")
    restaurant = cur.fetchone()

    conn.close()

    return restaurant

def reset_menu_to_starter():
    conn = get_db()
    cur = conn.cursor()

    starter_menu = [
        ("Starter Bites", "Appetizers", 6.99, "A customizable appetizer for your restaurant.", None),
        ("Signature Entree", "Entrees", 12.99, "A main dish that can be replaced with your own specialty.", None),
        ("House Dessert", "Desserts", 5.99, "A simple dessert placeholder for your custom menu.", None),
        ("House Drink", "Beverages", 2.99, "A starter beverage item for your menu.", None)
    ]

    cur.execute("DELETE FROM order_items")
    cur.execute("DELETE FROM menu")

    cur.executemany("""
        INSERT INTO menu (name, category, price, description, image_filename)
        VALUES (?, ?, ?, ?, ?)
    """, starter_menu)

    conn.commit()
    conn.close()

def menu_item_to_dict(item):
    return {
        "menu_id": item["menu_id"],
        "name": item["name"],
        "category": item["category"],
        "price": item["price"],
        "description": item["description"],
        "image_filename": item["image_filename"]
    }

def generate_ai_food_image(name, description, category):
    try:
        client = OpenAI()

        prompt = f"""
        Create a realistic, appetizing restaurant menu food photo.

        Food item name: {name}
        Category: {category}
        Description: {description}

        Style: professional food photography, clean background, realistic,
        well-lit, centered plate, high quality, restaurant menu image.
        Do not include text, labels, logos, or watermarks in the image.
        """

        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        image_b64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_b64)

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        filename = f"ai_food_{uuid.uuid4().hex}.png"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        with open(filepath, "wb") as image_file:
            image_file.write(image_bytes)

        return filename

    except Exception as e:
        print("AI image generation failed:", e)
        return None

@app.route("/")
def index():
    restaurant = get_restaurant()
    return render_template("index.html", restaurant=restaurant)

@app.route('/appetizers')
def appetizers():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM menu WHERE LOWER(category) = ?", ("appetizers",))
    menu = cur.fetchall()

    conn.close()

    return render_template('appetizers.html', menu=menu)


@app.route('/entrees')
def entrees():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM menu WHERE LOWER(category) = ?", ("entrees",))
    menu = cur.fetchall()

    conn.close()
    return render_template('entrees.html', menu=menu)

@app.route('/desserts')
def desserts():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM menu WHERE LOWER(category) = ?", ("desserts",))
    menu = cur.fetchall()

    conn.close()

    return render_template('desserts.html', menu=menu)


@app.route('/beverages')
def beverages():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM menu WHERE LOWER(category) = ?", ("beverages",))
    menu = cur.fetchall()

    conn.close()

    return render_template('beverages.html', menu=menu)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin_logged_in"):
        flash("Please log in to access the admin panel.", "warning")
        return redirect("/login")

    if request.method == "POST":
        image = request.files.get("image")

        image_url = upload_image_to_cloudinary(
            image,
            folder_name="restaurant_maker/menu"
        )

        category = request.form["category"].capitalize()

        new_menu_item = Menu(
            name=request.form["name"],
            category=category,
            price=float(request.form["price"]),
            description=request.form["description"],
            image_filename=None,
            image_url=image_url
        )

        db.session.add(new_menu_item)
        db.session.commit()

        flash("Menu item added successfully.", "success")
        return redirect("/admin")

    menu = (
        Menu.query
        .order_by(
            db.case(
                (db.func.lower(Menu.category) == "appetizers", 1),
                (db.func.lower(Menu.category) == "entrees", 2),
                (db.func.lower(Menu.category) == "desserts", 3),
                (db.func.lower(Menu.category) == "beverages", 4),
                else_=5
            ),
            Menu.name
        )
        .all()
    )

    return render_template("admin.html", menu=menu)

@app.route("/create-tables")
def create_tables():
    if not session.get("admin_logged_in"):
        flash("Please log in as admin first.", "warning")
        return redirect("/login")

    db.create_all()

    flash("Database tables created successfully.", "success")
    return redirect("/")

@app.route("/start_order", methods=["GET", "POST"])
def start_order():
    if not session.get("customer_id"):
        flash("Please log in before starting an order.", "warning")
        return redirect(url_for("customer_login"))

    customer_id = session["customer_id"]

    if request.method == "POST":
        order_number = "ABC" + datetime.now().strftime("%Y%m%d%H%M%S")
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_order = Order(
            customer_id=customer_id,
            order_number=order_number,
            date_time=date_time,
            status="Started",
            payment_method=None,
            total_amount=0
        )

        db.session.add(new_order)
        db.session.commit()

        session["order_number"] = order_number

        return redirect("/order")

    return render_template("start_order.html")

@app.route("/order", methods=["GET", "POST"])
def order():
    order_number = session.get("order_number")

    if not order_number:
        flash("Please start an order before choosing menu items.", "warning")
        return redirect("/start_order")

    if request.method == "POST":
        # Clear previous items for this order
        OrderItem.query.filter_by(order_number=order_number).delete()

        for key, value in request.form.items():
            if key.startswith("quantity_"):
                try:
                    quantity = int(value)
                except ValueError:
                    quantity = 0

                if quantity > 0:
                    menu_id = int(key.split("_")[1])

                    new_order_item = OrderItem(
                        order_number=order_number,
                        menu_id=menu_id,
                        quantity=quantity
                    )

                    db.session.add(new_order_item)

        db.session.commit()

        return redirect("/order_summary")

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = Menu.query

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Menu.name.ilike(search_pattern),
                Menu.description.ilike(search_pattern)
            )
        )

    if category:
        query = query.filter(db.func.lower(Menu.category) == category.lower())

    menu = query.order_by(
        db.case(
            (db.func.lower(Menu.category) == "appetizers", 1),
            (db.func.lower(Menu.category) == "entrees", 2),
            (db.func.lower(Menu.category) == "desserts", 3),
            (db.func.lower(Menu.category) == "beverages", 4),
            else_=5
        ),
        Menu.name
    ).all()

    restaurant = get_restaurant()

    return render_template(
        "order.html",
        menu=menu,
        restaurant=restaurant,
        search=search,
        selected_category=category
    )

@app.route("/order_summary")
def order_summary():
    order_number = session.get("order_number")

    if not order_number:
        flash("Please start an order first.", "warning")
        return redirect("/start_order")

    order_items = (
        db.session.query(
            Menu.name,
            Menu.price,
            OrderItem.quantity,
            (Menu.price * OrderItem.quantity).label("total_price")
        )
        .join(OrderItem, Menu.menu_id == OrderItem.menu_id)
        .filter(OrderItem.order_number == order_number)
        .all()
    )

    subtotal = sum(item.total_price for item in order_items)

    if subtotal > 0:
        tax = subtotal * 0.06625
        tip = subtotal * 0.15
        delivery_fee = 5
    else:
        tax = 0
        tip = 0
        delivery_fee = 0

    total = subtotal + tax + tip + delivery_fee

    return render_template(
        "order_summary.html",
        summary=order_items,
        subtotal=subtotal,
        tax=tax,
        tip=tip,
        delivery_fee=delivery_fee,
        total=total
    )

@app.route("/order-history")
def order_history():
    if not session.get("customer_id"):
        flash("Please log in to view your order history.", "warning")
        return redirect(url_for("customer_login"))

    customer_id = session["customer_id"]

    orders = (
        Order.query
        .filter_by(customer_id=customer_id)
        .order_by(Order.date_time.desc())
        .all()
    )

    return render_template("order_history.html", orders=orders)

@app.route("/order-history/<int:order_id>")
def order_details(order_id):
    if not session.get("customer_id"):
        flash("Please log in to view order details.", "warning")
        return redirect(url_for("customer_login"))

    customer_id = session["customer_id"]

    order = (
        Order.query
        .filter_by(order_id=order_id, customer_id=customer_id)
        .first()
    )

    if not order:
        flash("Order not found.", "warning")
        return redirect("/order-history")

    items = (
        db.session.query(
            Menu.name,
            Menu.price,
            OrderItem.quantity,
            (Menu.price * OrderItem.quantity).label("total_price")
        )
        .join(OrderItem, Menu.menu_id == OrderItem.menu_id)
        .filter(OrderItem.order_number == order.order_number)
        .all()
    )

    return render_template("order_details.html", order=order, items=items)

@app.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "password123":
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Admin logged in successfully.", "success")
            return redirect("/admin")

        flash("Invalid admin username or password.", "danger")
        return redirect("/login")

    return render_template("login.html")

@app.route("/customer-login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        customer = Customer.query.filter_by(email=email).first()

        if customer and check_password_hash(customer.password_hash, password):
            session["customer_id"] = customer.customer_id
            session["customer_name"] = customer.name
            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("customer_login"))

    return render_template("customer_login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        phone_number = request.form.get("phone_number")
        street_address = request.form.get("street_address")
        city = request.form.get("city")
        state = request.form.get("state")
        zip_code = request.form.get("zip_code")

        if not name or not email or not password:
            flash("Name, email, and password are required.", "warning")
            return redirect(url_for("register"))

        existing_customer = Customer.query.filter_by(email=email).first()

        if existing_customer:
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_customer = Customer(
            name=name,
            email=email,
            password_hash=password_hash,
            phone_number=phone_number,
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zip_code,
            created_at=created_at
        )

        db.session.add(new_customer)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("customer_login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("customer_id", None)
    session.pop("customer_name", None)

    flash("You have been logged out.", "info")
    return redirect("/")

@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)

    flash("Admin has been logged out.", "info")
    return redirect("/login")

@app.route("/restaurant_setup", methods=["GET", "POST"])
def restaurant_setup():
    if not session.get("admin_logged_in"):
        flash("Please log in to customize restaurant settings.", "warning")
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        theme_color = request.form["theme_color"]

        logo = request.files.get("logo")

        # Upload logo to Cloudinary instead of saving locally
        logo_url = upload_image_to_cloudinary(
            logo,
            folder_name="restaurant_maker/logos"
        )

        cur.execute("SELECT * FROM restaurants LIMIT 1")
        existing_restaurant = cur.fetchone()

        is_new_restaurant = existing_restaurant is None

        if existing_restaurant:
            if logo_url:
                cur.execute("""
                    UPDATE restaurants
                    SET name = ?, description = ?, theme_color = ?, logo_url = ?
                    WHERE restaurant_id = ?
                """, (
                    name,
                    description,
                    theme_color,
                    logo_url,
                    existing_restaurant["restaurant_id"]
                ))
            else:
                cur.execute("""
                    UPDATE restaurants
                    SET name = ?, description = ?, theme_color = ?
                    WHERE restaurant_id = ?
                """, (
                    name,
                    description,
                    theme_color,
                    existing_restaurant["restaurant_id"]
                ))
        else:
            cur.execute("""
                INSERT INTO restaurants
                (name, description, logo_filename, logo_url, theme_color, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                description,
                None,
                logo_url,
                theme_color,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        conn.commit()
        conn.close()

        if is_new_restaurant or request.form.get("reset_menu") == "yes":
            reset_menu_to_starter()
            flash("Restaurant profile saved and starter menu was created.", "success")
        else:
            flash("Restaurant profile saved successfully.", "success")

        return redirect("/restaurant_setup")

    cur.execute("SELECT * FROM restaurants LIMIT 1")
    restaurant = cur.fetchone()

    conn.close()

    return render_template("restaurant_setup.html", restaurant=restaurant)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    order_number = session.get("order_number")

    if not order_number:
        flash("Please start an order before checking out.", "warning")
        return redirect("/start_order")

    order_items = (
        db.session.query(
            Menu.name,
            Menu.price,
            OrderItem.quantity,
            (Menu.price * OrderItem.quantity).label("total_price")
        )
        .join(OrderItem, Menu.menu_id == OrderItem.menu_id)
        .filter(OrderItem.order_number == order_number)
        .all()
    )

    subtotal = sum(item.total_price for item in order_items)

    if subtotal <= 0:
        flash("Your cart is empty. Please add items before checking out.", "warning")
        return redirect("/order")

    tax = subtotal * 0.06625
    tip = subtotal * 0.15
    delivery_fee = 5
    total = subtotal + tax + tip + delivery_fee

    if request.method == "POST":
        try:
            line_items = []

            for item in order_items:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": item.name,
                        },
                        "unit_amount": int(round(item.price * 100)),
                    },
                    "quantity": item.quantity,
                })

            service_total = tax + tip + delivery_fee

            if service_total > 0:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Tax, Tip, and Delivery Fee",
                        },
                        "unit_amount": int(round(service_total * 100)),
                    },
                    "quantity": 1,
                })

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=url_for(
                    "payment_success",
                    _external=True
                ) + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=url_for("payment_cancel", _external=True),
                metadata={
                    "order_number": order_number
                }
            )

            order = Order.query.filter_by(order_number=order_number).first()

            if order:
                order.stripe_session_id = checkout_session.id
                order.stripe_payment_status = "created"
                order.total_amount = total
                order.status = "Pending Payment"

                db.session.commit()

            return redirect(checkout_session.url, code=303)

        except Exception as e:
            print("Stripe checkout error:", repr(e))
            flash("There was an error starting Stripe Checkout.", "danger")
            return redirect("/checkout")

    return render_template(
        "checkout.html",
        items=order_items,
        subtotal=subtotal,
        tax=tax,
        tip=tip,
        delivery_fee=delivery_fee,
        total=total
    )

@app.route("/payment-success")
def payment_success():
    stripe_session_id = request.args.get("session_id")

    if not stripe_session_id:
        flash("Missing Stripe session ID.", "warning")
        return redirect("/")

    try:
        checkout_session = stripe.checkout.Session.retrieve(stripe_session_id)

        order_number = checkout_session["metadata"]["order_number"]
        payment_status = checkout_session["payment_status"]

        order = Order.query.filter_by(order_number=order_number).first()

        if not order:
            flash("Order not found after payment.", "danger")
            return redirect("/")

        if payment_status == "paid":
            order.status = "Paid"
            order.stripe_payment_status = payment_status
            order.payment_method = "Stripe"

            db.session.commit()

            session["order_number"] = order_number

            flash("Payment successful! Your order has been placed.", "success")
            return redirect("/confirmation")

        flash("Payment was not completed.", "warning")
        return redirect("/checkout")

    except Exception as e:
        print("Stripe success error:", repr(e))
        flash(f"Could not verify payment: {e}", "danger")
        return redirect("/")
    
@app.route("/payment-cancel")
def payment_cancel():
    flash("Payment was canceled. You can try checking out again.", "warning")
    return redirect("/checkout")

@app.route("/confirmation")
def confirmation():
    order_number = session.get("order_number")

    if not order_number:
        flash("No completed order found.", "warning")
        return redirect("/start_order")

    order = Order.query.filter_by(order_number=order_number).first()

    if not order:
        flash("Order not found.", "warning")
        return redirect("/start_order")

    items = (
        db.session.query(
            Menu.name,
            Menu.price,
            OrderItem.quantity,
            (Menu.price * OrderItem.quantity).label("total_price")
        )
        .join(OrderItem, Menu.menu_id == OrderItem.menu_id)
        .filter(OrderItem.order_number == order_number)
        .all()
    )

    session.pop("order_number", None)

    return render_template(
        "confirmation.html",
        order=order,
        items=items
    )

@app.route("/clear_order")
def clear_order():
    order_number = session.get("order_number")

    if not order_number:
        flash("No active order to clear.", "warning")
        return redirect("/start_order")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM order_items
        WHERE order_number = ?
    """, (order_number,))

    conn.commit()
    conn.close()

    flash("Your order was cleared. You can now choose new items.", "info")
    return redirect("/order")

@app.route("/api/menu", methods=["GET"])
def api_get_menu():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM menu
        ORDER BY
            CASE LOWER(category)
                WHEN 'appetizers' THEN 1
                WHEN 'entrees' THEN 2
                WHEN 'desserts' THEN 3
                WHEN 'beverages' THEN 4
                ELSE 5
            END,
            name
    """)

    menu = cur.fetchall()
    conn.close()

    return jsonify([menu_item_to_dict(item) for item in menu])

@app.route("/api/menu/<int:menu_id>", methods=["GET"])
def api_get_menu_item(menu_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM menu
        WHERE menu_id = ?
    """, (menu_id,))

    item = cur.fetchone()
    conn.close()

    if item is None:
        return jsonify({"error": "Menu item not found"}), 404

    return jsonify(menu_item_to_dict(item))

@app.route("/api/menu", methods=["POST"])
def api_create_menu_item():
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Admin login required"}), 401

    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    required_fields = ["name", "category", "price", "description"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO menu (name, category, price, description, image_filename)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["category"].capitalize(),
        float(data["price"]),
        data["description"],
        data.get("image_filename")
    ))

    conn.commit()
    new_id = cur.lastrowid

    cur.execute("SELECT * FROM menu WHERE menu_id = ?", (new_id,))
    new_item = cur.fetchone()

    conn.close()

    return jsonify(menu_item_to_dict(new_item)), 201

@app.route("/api/menu/<int:menu_id>", methods=["PUT"])
def api_update_menu_item(menu_id):
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Admin login required"}), 401

    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM menu WHERE menu_id = ?", (menu_id,))
    existing_item = cur.fetchone()

    if existing_item is None:
        conn.close()
        return jsonify({"error": "Menu item not found"}), 404

    name = data.get("name", existing_item["name"])
    category = data.get("category", existing_item["category"])
    price = data.get("price", existing_item["price"])
    description = data.get("description", existing_item["description"])
    image_filename = data.get("image_filename", existing_item["image_filename"])

    cur.execute("""
        UPDATE menu
        SET name = ?, category = ?, price = ?, description = ?, image_filename = ?
        WHERE menu_id = ?
    """, (
        name,
        category.capitalize(),
        float(price),
        description,
        image_filename,
        menu_id
    ))

    conn.commit()

    cur.execute("SELECT * FROM menu WHERE menu_id = ?", (menu_id,))
    updated_item = cur.fetchone()

    conn.close()

    return jsonify(menu_item_to_dict(updated_item))

@app.route("/api/menu/<int:menu_id>", methods=["DELETE"])
def api_delete_menu_item(menu_id):
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Admin login required"}), 401

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM menu WHERE menu_id = ?", (menu_id,))
    item = cur.fetchone()

    if item is None:
        conn.close()
        return jsonify({"error": "Menu item not found"}), 404

    cur.execute("DELETE FROM menu WHERE menu_id = ?", (menu_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Menu item deleted successfully",
        "deleted_menu_id": menu_id
    })
    
@app.route("/ai_menu_generator", methods=["GET", "POST"])
def ai_menu_generator():
    if not session.get("admin_logged_in"):
        flash("Please log in to use the AI menu generator.", "warning")
        return redirect("/login")

    generated_items = session.get("generated_items", [])
    demo_mode = False

    if request.method == "POST":
        restaurant_type = request.form["restaurant_type"]
        item_count = int(request.form["item_count"])

        prompt = f"""
        Generate {item_count} restaurant menu items for this restaurant concept:
        {restaurant_type}

        Return ONLY valid JSON in this exact format:
        [
          {{
            "name": "Item Name",
            "category": "Appetizers",
            "price": 9.99,
            "description": "Short menu description"
          }}
        ]

        Categories must be one of:
        Appetizers, Entrees, Desserts, Beverages.
        Prices should be realistic.
        """

        try:
            client = OpenAI()
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt
            )

            generated_text = response.output_text
            generated_items = json.loads(generated_text)

        except Exception:
            demo_mode = True

            flash(
                "AI quota unavailable, so demo menu ideas were generated instead.",
                "warning"
            )

            sample_items = [
                {
                    "name": "Crispy Loaded Nachos",
                    "category": "Appetizers",
                    "price": 10.99,
                    "description": "Tortilla chips topped with melted cheese, jalapeños, salsa, and house crema."
                },
                {
                    "name": "Signature Grill Burger",
                    "category": "Entrees",
                    "price": 14.99,
                    "description": "Juicy grilled burger with lettuce, tomato, onions, pickles, and house sauce."
                },
                {
                    "name": "Chocolate Lava Cake",
                    "category": "Desserts",
                    "price": 7.99,
                    "description": "Warm chocolate cake with a rich melted center served with whipped cream."
                }
            ]

            generated_items = sample_items[:item_count]

        session["generated_items"] = generated_items

    return render_template(
        "ai_menu_generator.html",
        generated_items=generated_items,
        demo_mode=demo_mode
    )

@app.route("/save_ai_menu_item", methods=["POST"])
def save_ai_menu_item():
    if not session.get("admin_logged_in"):
        flash("Please log in to save AI menu items.", "warning")
        return redirect("/login")

    name = request.form["name"]
    category = request.form["category"]
    price = float(request.form["price"])
    description = request.form["description"]

    generate_image = request.form.get("generate_image") == "yes"

    image_filename = None

    if generate_image:
        image_filename = generate_ai_food_image(name, description, category)

        if image_filename:
            flash("AI image generated successfully.", "success")
        else:
            flash("Menu item was saved, but AI image generation failed.", "warning")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO menu (name, category, price, description, image_filename)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        category,
        price,
        description,
        image_filename
    ))

    conn.commit()
    conn.close()

    flash(f"{name} was added to your menu.", "success")

    return redirect("/ai_menu_generator")

@app.route("/clear_ai_items")
def clear_ai_items():
    if not session.get("admin_logged_in"):
        flash("Please log in first.", "warning")
        return redirect("/login")

    session.pop("generated_items", None)

    flash("Generated AI items cleared.", "info")
    return redirect("/ai_menu_generator")

@app.route("/admin/analytics")
def admin_analytics():
    if not session.get("admin_logged_in"):
        flash("Please log in to view analytics.", "warning")
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # Total orders and revenue
    cur.execute("""
        SELECT 
            COUNT(*) AS total_orders,
            COALESCE(SUM(total_amount), 0) AS total_revenue,
            COALESCE(AVG(total_amount), 0) AS average_order_value
        FROM orders
        WHERE status = 'Paid'
    """)
    summary = cur.fetchone()

    # Most popular menu items
    cur.execute("""
        SELECT 
            m.name,
            m.category,
            SUM(oi.quantity) AS total_sold,
            SUM(oi.quantity * m.price) AS item_revenue
        FROM order_items oi
        JOIN menu m ON oi.menu_id = m.menu_id
        GROUP BY m.menu_id, m.name, m.category
        ORDER BY total_sold DESC
        LIMIT 5
    """)
    popular_items = cur.fetchall()

    # Recent orders
    cur.execute("""
        SELECT 
            o.order_number,
            o.date_time,
            o.status,
            o.payment_method,
            o.total_amount,
            c.name AS customer_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        ORDER BY o.date_time DESC
        LIMIT 10
    """)
    recent_orders = cur.fetchall()

    # Top customers by spending
    cur.execute("""
        SELECT 
            c.name,
            c.email,
            COUNT(o.order_id) AS order_count,
            COALESCE(SUM(o.total_amount), 0) AS total_spent
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.status = 'Paid'
        GROUP BY c.customer_id, c.name, c.email
        ORDER BY total_spent DESC
        LIMIT 5
    """)
    top_customers = cur.fetchall()

    conn.close()

    return render_template(
        "admin_analytics.html",
        summary=summary,
        popular_items=popular_items,
        recent_orders=recent_orders,
        top_customers=top_customers
    )

if __name__ == "__main__":
    app.run(debug=True, port=5001)