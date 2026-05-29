# Custom Restaurant Maker

Custom Restaurant Maker is a full-stack Flask web application that allows restaurant owners/admins to customize a restaurant profile, manage menu items, upload food images, generate AI-powered menu ideas, and process customer orders through a checkout flow.

This project was built as a portfolio-ready restaurant management and ordering platform using Flask, SQLite, Bootstrap, Jinja, REST-style API routes, and OpenAI API integration.

---

## Live Demo

Live Site: https://custom-restaurant-maker.onrender.com

GitHub Repository: https://github.com/amcaaron/custom-restaurant-maker

---

## Features

### Restaurant Customization

* Create and update a restaurant profile
* Add restaurant name, description, theme color, and logo
* Reset the menu back to starter/default menu items
* Homepage dynamically displays restaurant branding
* Starter menu encourages users to create their own custom menu

### Admin Authentication

* Admin login and logout system
* Protected admin dashboard
* Password hashing using Werkzeug
* Session-based authentication
* Flash messages for login, logout, and protected routes

### Menu Management

* Add menu items manually through the admin panel
* Upload images for menu items
* Organize menu items by category:

  * Appetizers
  * Entrees
  * Desserts
  * Beverages
* View menu items in a Bootstrap card layout
* Dynamically display menu items from the SQLite database

### AI Menu Generator

* Generate AI-powered menu item ideas based on a restaurant concept
* Generate item name, category, price, and description
* Save generated items directly to the real menu
* Optionally generate AI food images for menu items
* Demo fallback mode if AI quota/API is unavailable

### Customer Ordering Flow

* Start an order as a new or existing customer
* Select menu item quantities
* View order summary
* Clear order and return to menu
* Checkout with payment method selection
* View order confirmation
* Prevents users from ordering before starting a customer/order session

### Checkout System

* Calculates subtotal
* Calculates NJ sales tax
* Adds tip and delivery fee when applicable
* Avoids adding tax, tip, and delivery fee for empty carts
* Saves payment method and total amount
* Displays final confirmation page

### REST API Routes

The project includes REST-style backend endpoints for menu management:

GET    /api/menu
GET    /api/menu/<id>
POST   /api/menu
PUT    /api/menu/<id>
DELETE /api/menu/<id>

These routes allow menu data to be retrieved, created, updated, and deleted using JSON requests.

---

## Tech Stack

### Backend

* Python
* Flask
* SQLite
* Jinja2
* Werkzeug Security
* OpenAI API

### Frontend

* HTML5
* CSS3
* Bootstrap 5
* Jinja Templates
* Custom Styling

### Tools and Deployment

* VS Code
* Git
* GitHub
* Render
* Thunder Client
* Gunicorn
* OpenAI Platform

---

## Project Structure

RestarantProject/

├── app.py
├── init_db.py
├── project4.db
├── requirements.txt
├── Procfile
├── README.md
├── .gitignore

├── static/
│   ├── style.css
│   └── uploads/

└── templates/
├── admin.html
├── ai_menu_generator.html
├── appetizers.html
├── base.html
├── beverages.html
├── checkout.html
├── confirmation.html
├── desserts.html
├── entrees.html
├── index.html
├── login.html
├── order.html
├── order_summary.html
├── restaurant_setup.html
└── start_order.html

---

## Setup Instructions

### 1. Clone the Repository

git clone https://github.com/amcaaron/custom-restaurant-maker.git

cd custom-restaurant-maker

### 2. Create a Virtual Environment

python -m venv venv

Activate the environment:

Mac/Linux:

source venv/bin/activate

Windows:

venv\Scripts\activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Initialize the Database

python init_db.py

### 5. Create a .env File

Create a file named:

.env

Add:

OPENAI_API_KEY=your_openai_api_key_here

### 6. Run the Application

python app.py

Open your browser and navigate to:

http://127.0.0.1:5001/

---

## Admin Login

Demo Admin Credentials:

Username: admin

Password: password123

Note: These credentials should be changed before production deployment.

---

## API Testing

The REST API can be tested using:

* Thunder Client
* Postman
* curl

### Get All Menu Items

curl http://127.0.0.1:5001/api/menu

### Get One Menu Item

curl http://127.0.0.1:5001/api/menu/1

### Example JSON for Creating a Menu Item

{
"name": "Test Fries",
"category": "Appetizers",
"price": 5.99,
"description": "Crispy fries created through the API",
"image_filename": null
}

---

## Deployment

This project is deployed using Render.

### Render Build Settings

Build Command:

pip install -r requirements.txt

Start Command:

gunicorn app:app

---

## Important Deployment Notes

This project currently uses:

* SQLite
* Local image uploads

Because Render's free tier uses an ephemeral filesystem:

* Uploaded images may not persist permanently after redeployments
* Database changes made directly on the deployed application may not survive redeployments

For production use, recommended upgrades include:

* PostgreSQL database
* Cloudinary image storage
* AWS S3 image storage
* Persistent cloud database hosting

---

## Future Improvements

Potential future enhancements:

* Customer account registration
* Customer login system
* PostgreSQL integration
* Cloud image storage
* Stripe payment processing
* Restaurant analytics dashboard
* Menu search and filtering
* Order history page
* Multiple restaurant support
* AI-generated restaurant themes
* AI-generated menu categories
* Enhanced AI customization controls

---

## Key Skills Demonstrated

* Flask backend development
* SQLite database design
* CRUD operations
* Authentication and session management
* REST API development
* File and image uploads
* OpenAI API integration
* Bootstrap UI development
* Deployment with Render
* Git and GitHub workflow
* Full-stack web development
