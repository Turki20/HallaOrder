# 🍽️ HalaOrder – Restaurant Ordering & Management Platform

HalaOrder is a multi-tenant platform built with **Django** that helps restaurants create their own online store, manage menus, process orders, and receive payments.  
It also provides dashboards for platform admins, restaurant owners, and staff, as well as a simple customer-facing interface for online ordering.

---

## 🚀 Features (MVP)
### 👤 Users
- Role-based authentication (Admin, RestaurantOwner, Customer).
- Manage staff accounts (future extension).

### 🏢 Restaurants
- Register restaurants with subscription plans.
- Manage multiple branches.
- Auto-generate QR codes for dine-in ordering.

### 📋 Menu
- Categories & Products.
- Product options (sizes, spice level, etc.).
- Add-ons (extra cheese, sauces, etc.).
- Enable/disable items in real-time.

### 🛒 Orders
- Customers can place orders via QR code (dine-in) or pickup.
- Restaurant owners can manage order statuses:
  - **New → Preparing → Ready → Delivered → Cancelled**
- Order history for customers.

### 💳 Payments (Next Phase)
- Integration with Mada, Apple Pay, Visa, and Cash.
- ZATCA-compliant invoices.

### 📊 Reports & Analytics (Next Phase)
- Restaurant performance reports.
- Platform-wide analytics (total orders, revenue, growth trends).

---

## 🏗️ Project Structure
```
halaorder/
│── manage.py
│── halaorder/         # Project settings & configs
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
│── users/             # Authentication & roles
│── restaurants/       # Restaurants, branches, subscriptions
│── menu/              # Categories, products, add-ons
│── orders/            # Orders & order items
│
└── README.md
```

---

## 📖 User Stories Covered (MVP)
- **Platform Admin**: Manage restaurants and subscription plans.
- **Restaurant Owner**: Register restaurant, set up branches, create digital menu, process orders.
- **Customer**: Browse menu, place order (pickup/QR dine-in), track order status.

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/halaorder.git
cd halaorder
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Create a superuser
```bash
python manage.py createsuperuser
```

### 6. Start the development server
```bash
python manage.py runserver
```

Now visit:  
- Admin Panel → `http://127.0.0.1:8000/admin/`  
- Restaurant/Customer app → `http://127.0.0.1:8000/`  

---

## 📌 Roadmap
- [x] MVP: Users, Restaurants, Menu, Orders.  
- [ ] Payments integration.  
- [ ] Invoices (ZATCA compliance).  
- [ ] Reports & Analytics dashboards.  
- [ ] POS System integration.  
- [ ] Delivery partner integration.  

---

## 👥 Contributors
- **Platform Owner / Developer:** [Your Name]  

---

## 📜 License
This project is licensed under the MIT License.
