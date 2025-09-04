# HalaOrder – Restaurant Ordering & Management Platform

HalaOrder is a multi-tenant platform built with **Django** that helps restaurants create their own online store, manage menus, process orders, and receive payments.  
It also provides dashboards for platform admins, restaurant owners, and staff, as well as a simple customer-facing interface for online ordering.

## Market study
[HalaOrder](https://github.com/user-attachments/files/22133622/HalaOrder.pdf)


---

## 🚀 Features (MVP)
### Users
- Role-based authentication (Admin, RestaurantOwner, Customer).
- Manage staff accounts (future extension).

### Restaurants
- Register restaurants with subscription plans.
- Manage multiple branches.

### Menu
- Categories & Products.
- Product options (sizes, spice level, etc.).
- Add-ons (extra cheese, sauces, etc.).
- Enable/disable items in real-time.

### Orders
- Customers can place orders via QR code (dine-in) or pickup.
- Restaurant owners can manage order statuses:
  - **New → Preparing → Ready → Delivered → Cancelled**
- Order history for customers.

### Payments 
- Integration with Mada, Apple Pay, Visa, and Cash.

### Reports & Analytics 
- Restaurant performance reports.
- Platform-wide analytics (total orders, revenue, growth trends).

---

## Project Structure
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
│── payments/          
│── reports/           
│── websites/           
│── home/           
│
└── README.md
```

---

## User Stories Covered (MVP)
- **Platform Admin**: Manage restaurants and subscription plans.
- **Restaurant Owner**: Register restaurant, set up branches, create digital menu, process orders.
- **Customer**: Browse menu, place order (pickup/QR dine-in), track order status.
- [system analysis](https://github.com/user-attachments/files/22133509/system.analysis.pdf)

## System Design
### ERD
- <img width="1301" height="521" alt="image" src="https://github.com/user-attachments/assets/005f4268-afe1-4c20-9edd-daaa5cd118db" />
- <img width="1238" height="977" alt="image" src="https://github.com/user-attachments/assets/5d12b4ba-252f-41c9-bf52-5203ff03c254" />
---
### wirframe
- <img width="992" height="1077" alt="image" src="https://github.com/user-attachments/assets/af522d31-b6e4-4a46-a4e3-6b8262c0f02a" />
- <img width="996" height="811" alt="image" src="https://github.com/user-attachments/assets/5e7a2894-126e-42fe-b35f-4a372fcc8cca" />


---

## Installation & Setup

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

---

