# Custom Restaurant Maker

Custom Restaurant Maker is a full-stack Flask web application that allows a restaurant admin to customize a restaurant profile, manage menu items, upload food images, generate AI-powered menu ideas, generate AI food images, accept customer orders, process payments through Stripe, and view restaurant analytics.

This project was built as a portfolio-ready restaurant ordering and management platform using Flask, SQLAlchemy, PostgreSQL, Bootstrap, Jinja templates, Cloudinary, Stripe, OpenAI, and Render.

## Live Demo

**Live Site:** https://customizable-restaurant-maker.onrender.com

**GitHub Repository:** https://github.com/amcaaron/custom-restaurant-maker

---

## Features

### Restaurant Customization

* Create and update a restaurant profile
* Add restaurant name, description, logo, and theme color
* Dynamically apply the selected theme color across the app
* Display restaurant branding on the homepage and order pages
* Reset the menu back to starter/default menu items

### Admin Authentication

* Admin login and logout system
* Protected admin dashboard
* Admin credentials stored securely through environment variables
* Session-based authentication
* Flash messages for login, logout, and protected routes

### Customer Accounts

* Customer registration
* Customer login and logout
* Customer-specific order history
* Customers must be logged in before starting an order
* Password hashing using Werkzeug security tools

### Menu Management

* Add menu items manually through the admin panel
* Upload menu item images through Cloudinary
* Organize menu items by category:

  * Appetizers
  * Entrees
  * Desserts
  * Beverages
* View menu items in a Bootstrap card layout
* Menu items are stored in a PostgreSQL database on deployment
* Menu images persist through Cloudinary instead of local file storage

### AI Menu Generator

* Generate AI-powered menu item ideas based on a restaurant concept
* Generate item name, category, price, and description
* Save generated AI items directly to the real menu
* Optionally generate AI food images for menu items
* AI-generated images are uploaded to Cloudinary
* Demo fallback mode is included if AI quota or API access is unavailable

### Customer Ordering Flow

* Register or log in as a customer
* Start an order
* Select menu item quantities
* View order summary
* Clear order and return to the menu
* Checkout through Stripe
* View final order confirmation
* View previous orders through customer order history

### Checkout and Payment System

* Calculates subtotal
* Calculates NJ sales tax
* Adds tip and delivery fee when applicable
* Prevents checkout for empty carts
* Processes card payments through Stripe Checkout
* Saves payment method, payment status, and total amount
* Redirects customers to a confirmation page after successful payment

### Admin Analytics Dashboard

* View total paid orders
* View total revenue
* View average order value
* View most popular menu items
* View recent orders
* View top customers by spending

### REST API Routes

The project includes REST-style backend endpoints for menu management.

| Method | Endpoint              | Description                                   |
| ------ | --------------------- | --------------------------------------------- |
| GET    | `/api/menu`           | Get all menu items                            |
| GET    | `/api/menu/<menu_id>` | Get one menu item                             |
| POST   | `/api/menu`           | Create a new menu item                        |
| PUT    | `/api/menu/<menu_id>` | Update a menu item                            |
| DELETE | `/api/menu/<menu_id>` | Delete a menu item if it has not been ordered |

These routes allow menu data to be retrieved, created, updated, and deleted using JSON requests.

---

## Tech Stack

### Backend

* Python
* Flask
* Flask-SQLAlchemy
* PostgreSQL
* SQLite for local development fallback
* Jinja2
* Werkzeug Security
* OpenAI API
* Stripe API
* Cloudinary API

### Frontend

* HTML5
* CSS3
* Bootstrap 5
* Jinja Templates
* Custom CSS styling
* Dynamic theme color support

### Tools and Deployment

* VS Code
* Git
* GitHub
* Render
* Render PostgreSQL
* Gunicorn
* Thunder Client / Postman
* Cloudinary
* Stripe Dashboard
* OpenAI Platform

---

## Project Structure

```text
custom-restaurant-maker/

├── app.py
├── requirements.txt
├── Procfile
├── README.md
├── .gitignore
├── project4.db
│
├── static/
│   ├── style.css
│   └── uploads/
│
└── templates/
    ├── admin.html
    ├── admin_analytics.html
    ├── ai_menu_generator.html
    ├── base.html
    ├── checkout.html
    ├── confirmation.html
    ├── customer_login.html
    ├── index.html
    ├── login.html
    ├── order.html
    ├── order_details.html
    ├── order_history.html
    ├── order_summary.html
    ├── register.html
    ├── restaurant_setup.html
    └── start_order.html
```

---

## Database Models

The app uses SQLAlchemy models for:

* Customers
* Menu items
* Orders
* Order items
* Restaurant profile

In local development, the app can fall back to SQLite. In production, it uses PostgreSQL through Render.

---

## Environment Variables

Create a `.env` file locally and add the following variables:

```env
SECRET_KEY=your_secret_key

ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password

DATABASE_URL=your_database_url_optional_for_local_postgres

CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

STRIPE_SECRET_KEY=your_stripe_secret_key

OPENAI_API_KEY=your_openai_api_key
```

For local SQLite development, `DATABASE_URL` can be left out. The app will use `project4.db` automatically.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/amcaaron/custom-restaurant-maker.git
cd custom-restaurant-maker
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment.

Mac/Linux:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` File

Create a file named `.env` in the root folder and add the required environment variables.

Example:

```env
SECRET_KEY=your_secret_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
STRIPE_SECRET_KEY=your_stripe_secret_key
OPENAI_API_KEY=your_openai_api_key
```

### 5. Initialize the Database

```bash
flask --app app init-db
```

You should see:

```text
Database tables created successfully.
```

### 6. Run the Application Locally

```bash
python app.py
```

Open your browser and navigate to:

```text
http://127.0.0.1:5001/
```

---

## Admin Login

Admin credentials are controlled through environment variables:

```env
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
```

For security, admin credentials should not be hardcoded in the source code or committed to GitHub.

---

## Stripe Test Payment

For testing checkout, use Stripe’s test card:

```text
Card Number: 4242 4242 4242 4242
Expiration Date: Any future date
CVC: Any 3 digits
ZIP: Any ZIP code
```

---

## API Testing

The REST API can be tested using:

* Thunder Client
* Postman
* curl

### Get All Menu Items

```bash
curl http://127.0.0.1:5001/api/menu
```

### Get One Menu Item

```bash
curl http://127.0.0.1:5001/api/menu/1
```

### Example JSON for Creating a Menu Item

```json
{
  "name": "Test Fries",
  "category": "Appetizers",
  "price": 5.99,
  "description": "Crispy fries created through the API",
  "image_filename": null,
  "image_url": null
}
```

---

## Deployment

This project is deployed using Render.

### Render Build Settings

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app --timeout 180 --workers 1
```

The extended timeout is used because AI food image generation can take longer than a standard request.

### Render Environment Variables

The deployed Render web service should include:

```env
SECRET_KEY=your_secret_key
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
DATABASE_URL=your_render_postgresql_internal_database_url
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
STRIPE_SECRET_KEY=your_stripe_secret_key
OPENAI_API_KEY=your_openai_api_key
```

### Database Setup on Render

After connecting the Render PostgreSQL database, initialize the production database with:

```bash
flask --app app init-db
```

If shell access is unavailable, this can be run temporarily through the Render build command:

```bash
pip install -r requirements.txt && flask --app app init-db
```

After the tables are created, the build command should be changed back to:

```bash
pip install -r requirements.txt
```

---

## Production Notes

This project uses:

* PostgreSQL for persistent production data
* Cloudinary for persistent image storage
* Stripe Checkout for payment processing
* OpenAI for menu and image generation
* Render for deployment

Local uploaded files are not relied on in production because Render’s filesystem can be temporary. Images are stored through Cloudinary instead.

---

## Current Limitations

This version is designed as a single-restaurant platform.

That means:

* One admin controls the restaurant profile
* One shared restaurant menu is used
* Multiple customers can register and place orders
* Customers do not each get their own restaurant

A future version could add multi-restaurant support where each restaurant owner has their own restaurant profile, menu, orders, and analytics.

---

## Future Improvements

Potential future enhancements include:

* Multi-restaurant / multi-owner support
* Owner registration and role-based permissions
* Stripe webhooks for more production-grade payment confirmation
* Better order status tracking
* Email receipts
* Customer profile editing
* Admin order management dashboard
* Unit and integration tests
* Custom 404 and 500 error pages
* Background job processing for AI image generation
* More advanced AI customization controls

---

## Key Skills Demonstrated

* Full-stack web development
* Flask backend development
* SQLAlchemy ORM design
* PostgreSQL database integration
* Customer authentication
* Admin authentication
* Password hashing
* Session management
* CRUD operations
* REST API development
* Cloudinary image storage
* Stripe payment integration
* OpenAI API integration
* AI-generated content and image workflows
* Bootstrap UI development
* Jinja templating
* Render deployment
* Environment variable management
* Git and GitHub workflow

---

## Project Summary

Custom Restaurant Maker is a deployed full-stack restaurant ordering platform that combines restaurant customization, admin menu management, customer ordering, payment processing, analytics, image storage, and AI-powered menu generation into one web application.

The project demonstrates practical backend development, database design, API development, third-party service integration, production deployment, and user-focused full-stack design.

