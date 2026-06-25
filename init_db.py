# import sqlite3
# from datetime import datetime

# # Define SQL schema
# schema = """

# CREATE TABLE menu (
#     menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     category TEXT NOT NULL,
#     price REAL NOT NULL,
#     description TEXT
# );

# CREATE TABLE customers (
#     customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     street_address TEXT,
#     city TEXT,
#     state TEXT,
#     zip_code TEXT,
#     phone_number TEXT
# );

# CREATE TABLE orders (
#     order_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     customer_id INTEGER NOT NULL,
#     order_number TEXT UNIQUE NOT NULL,
#     date_time TEXT NOT NULL,
#     FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
# );

# CREATE TABLE order_items (
#     order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     order_number TEXT NOT NULL,
#     menu_id INTEGER NOT NULL,
#     quantity INTEGER NOT NULL,
#     FOREIGN KEY (order_number) REFERENCES orders(order_number),
#     FOREIGN KEY (menu_id) REFERENCES menu(menu_id)
# );
# """

# # Test data
# test_menu = [
#     # Appetizers
#     ("Calamari", "appetizers", 19.99, "Crispy squid served with marinara sauce"),
#     ("Garlic Bread", "appetizers", 10.50, "Freshly baked bread served with garlic butter"),
#     ("Mozzarella Sticks", "appetizers", 12.99, "Golden fried mozzarella with marinara"),
#     ("Chicken Wings", "appetizers", 14.99, "Buffalo wings served with ranch"),

#     # Entrees
#     ("Grilled Salmon", "entrees", 24.99, "Fresh salmon served with vegetables and rice"),
#     ("Steak Frites", "entrees", 29.99, "Grilled ribeye steak with French fries"),
#     ("Chicken Alfredo", "entrees", 21.50, "Pasta with creamy Alfredo sauce and grilled chicken"),
#     ("Veggie Burger", "entrees", 18.75, "Plant-based burger with lettuce, tomato, and avocado"),

#     # Desserts
#     ("Cheesecake", "desserts", 8.99, "Classic New York-style cheesecake"),
#     ("Chocolate Lava Cake", "desserts", 9.50, "Molten chocolate cake served with vanilla ice cream"),
#     ("Apple Pie", "desserts", 7.25, "Warm apple pie with cinnamon and crust"),
#     ("Tiramisu", "desserts", 8.50, "Coffee-flavored Italian dessert with mascarpone cream"),

#     # Beverages
#     ("Coke", "beverages", 2.99, "Chilled Coca-Cola"),
#     ("Lemonade", "beverages", 3.50, "Fresh squeezed lemonade"),
#     ("Iced Tea", "beverages", 2.75, "Cold brewed iced tea"),
#     ("Orange Juice", "beverages", 3.95, "100% pure orange juice")
# ]

# test_customer = (
#     "Alex", "1000 Morris Avenue", "Union", "NJ", "07083", "908-737-5326"
# )

# # Connect and execute
# conn = sqlite3.connect("project4.db")
# cursor = conn.cursor()

# # Run schema
# cursor.executescript(schema)
# print("Database schema created.")

# # Insert one menu item
# cursor.executemany(
#     """INSERT INTO menu (name, category, price, description)
#     VALUES (?, ?, ?, ?)""", test_menu
# )

# # Insert one test customer
# cursor.execute(
#     """INSERT INTO customers (name, street_address, city, state, zip_code, phone_number)
#        VALUES (?, ?, ?, ?, ?, ?)""", test_customer
# )

# conn.commit()
# conn.close()
# print("Inserted sample menu and one test customer into project6.db.")

