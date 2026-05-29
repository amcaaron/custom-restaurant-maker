import os
import sqlite3
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mysecretkey"  # Needed for session handling

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


def get_restaurant():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM restaurants LIMIT 1")
    restaurant = cur.fetchone()

    conn.close()

    return restaurant

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

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        image = request.files.get("image")
        image_filename = None

        if image and image.filename != "" and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)

            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
            image.save(image_path)

        category = request.form["category"].capitalize()

        cur.execute("""
            INSERT INTO menu (name, category, price, description, image_filename)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["name"],
            category,
            float(request.form["price"]),
            request.form["description"],
            image_filename
        ))

        conn.commit()

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

    return render_template("admin.html", menu=menu)

@app.route("/start_order", methods=["GET", "POST"])
def start_order():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        if request.form["type"] == "new":
            cur.execute("INSERT INTO customers (name, street_address, city, state, zip_code, phone_number) VALUES (?, ?, ?, ?, ?, ?)",
                        (request.form["name"], request.form["street_address"], request.form["city"], request.form["state"], request.form["zip_code"], request.form["phone_number"]))
            customer_id = cur.lastrowid
        else:
            cur.execute("SELECT customer_id FROM customers WHERE name = ?", (request.form["name"],))
            row = cur.fetchone()
            if row:
                customer_id = row["customer_id"]
            else:
                return "Customer not found"
        order_number = "ABC" + datetime.now().strftime('%Y%m%d%H%M%S')
        date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO orders (customer_id, order_number, date_time) VALUES (?, ?, ?)",
                    (customer_id, order_number, date_time))
        conn.commit()
        session["order_number"] = order_number
        return redirect("/order")
    return render_template("start_order.html")

@app.route("/order", methods=["GET", "POST"])
def order():
    order_number = session.get("order_number")

    if not order_number:
        flash("Please start an order before choosing menu items.", "warning")
        return redirect("/start_order")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        cur.execute("""
            DELETE FROM order_items
            WHERE order_number = ?
        """, (order_number,))

        for key, value in request.form.items():

            if key.startswith("quantity_"):

                try:
                    quantity = int(value)
                except ValueError:
                    quantity = 0

                if quantity > 0:
                    menu_id = int(key.split("_")[1])

                    cur.execute("""
                        INSERT INTO order_items
                        (order_number, menu_id, quantity)
                        VALUES (?, ?, ?)
                    """, (
                        order_number,
                        menu_id,
                        quantity
                    ))

        conn.commit()
        conn.close()

        return redirect("/order_summary")

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

    restaurant = get_restaurant()

    return render_template("order.html", menu=menu, restaurant=restaurant)

@app.route("/order_summary")
@app.route("/order_summary")
def order_summary():
    conn = get_db()
    cur = conn.cursor()

    order_number = session.get("order_number")

    if not order_number:
        flash("Please start an order first.", "warning")
        return redirect("/start_order")

    cur.execute("""
        SELECT m.name, m.price, oi.quantity, (m.price * oi.quantity) AS total_price
        FROM order_items oi
        JOIN menu m ON m.menu_id = oi.menu_id
        WHERE oi.order_number = ?
    """, (order_number,))

    items = cur.fetchall()

    subtotal = sum(item["total_price"] for item in items)

    if subtotal > 0:
        tax = subtotal * 0.06625
        tip = subtotal * 0.15
        delivery_fee = 5
    else:
        tax = 0
        tip = 0
        delivery_fee = 0

    total = subtotal + tax + tip + delivery_fee

    conn.close()

    return render_template(
        "order_summary.html",
        summary=items,
        subtotal=subtotal,
        tax=tax,
        tip=tip,
        delivery_fee=delivery_fee,
        total=total
    )
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM admins
            WHERE username = ?
        """, (username,))

        admin = cur.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_logged_in"] = True
            session["admin_username"] = admin["username"]

            flash("Login successful.", "success")
            return redirect("/admin")
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)

    flash("You have been logged out.", "info")
    return redirect("/")

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
        logo_filename = None

        if logo and logo.filename != "" and allowed_file(logo.filename):
            logo_filename = secure_filename(logo.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            logo.save(os.path.join(app.config["UPLOAD_FOLDER"], logo_filename))

        cur.execute("SELECT * FROM restaurants LIMIT 1")
        existing_restaurant = cur.fetchone()

        if existing_restaurant:
            if logo_filename:
                cur.execute("""
                    UPDATE restaurants
                    SET name = ?, description = ?, theme_color = ?, logo_filename = ?
                    WHERE restaurant_id = ?
                """, (
                    name,
                    description,
                    theme_color,
                    logo_filename,
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
                (name, description, logo_filename, theme_color, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                description,
                logo_filename,
                theme_color,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        conn.commit()
        conn.close()

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

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.name, m.price, oi.quantity, (m.price * oi.quantity) AS total_price
        FROM order_items oi
        JOIN menu m ON m.menu_id = oi.menu_id
        WHERE oi.order_number = ?
    """, (order_number,))

    items = cur.fetchall()

    subtotal = sum(item["total_price"] for item in items)
    tax = subtotal * 0.06625
    tip = subtotal * 0.15
    delivery_fee = 5
    total = subtotal + tax + tip + delivery_fee

    if request.method == "POST":
        payment_method = request.form["payment_method"]

        cur.execute("""
            UPDATE orders
            SET status = ?, payment_method = ?, total_amount = ?
            WHERE order_number = ?
        """, (
            "Paid",
            payment_method,
            total,
            order_number
        ))

        conn.commit()
        conn.close()

        return redirect("/confirmation")

    conn.close()

    return render_template(
        "checkout.html",
        items=items,
        subtotal=subtotal,
        tax=tax,
        tip=tip,
        delivery_fee=delivery_fee,
        total=total
    )

@app.route("/confirmation")
def confirmation():
    order_number = session.get("order_number")

    if not order_number:
        flash("No completed order found.", "warning")
        return redirect("/start_order")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM orders
        WHERE order_number = ?
    """, (order_number,))

    order = cur.fetchone()

    cur.execute("""
        SELECT m.name, m.price, oi.quantity, (m.price * oi.quantity) AS total_price
        FROM order_items oi
        JOIN menu m ON m.menu_id = oi.menu_id
        WHERE oi.order_number = ?
    """, (order_number,))

    items = cur.fetchall()

    conn.close()

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

if __name__ == "__main__":
    app.run(debug=True, port=5001)