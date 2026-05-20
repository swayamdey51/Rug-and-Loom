import os
import shutil
import sqlite3
import json
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__)

# ─── AUTO-DETECT CONFIGURATION PATHS ───
# Establishes the server workspace folder relative to this file's position
PROJECT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT, 'uploads', 'images')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure asset directory hierarchy exists safely
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def initialize_assets():
    """Validates and stages local visual media blocks into the asset engine directory."""
    images_to_copy = [
        'Carpet1.jpg', 'Carpet2.jpg', 'Carpet3.jpg', 'Carpet4.jpg',
        'Carpet5.jpg', 'Carpet6.jpg', 'Carpet7.jpg', 'Pahaad.jpg', 'Hero.jpg',
        'Nikki.JPG', 'Swayam.JPG', 'OurStory.JPG', 'Loading.PNG'
    ]
    print("\n--- Initializing image assets ---")
    for img in images_to_copy:
        dest = os.path.join(UPLOAD_FOLDER, img)
        if os.path.exists(dest):
            print(f"  [OK] {img} already in uploads/images")
        elif os.path.exists(img):
            shutil.copy(img, dest)
            print(f"  [COPIED] {img} -> uploads/images")
        else:
            print(f"  [WARNING] {img} not found!")
    print("  All images ready. Server starting...\n")


def initialize_database():
    """Establishes data columns supporting shipping destinations, logistics tracks, and reviews."""
    conn = sqlite3.connect(os.path.join(PROJECT, 'orders.db'))
    cursor = conn.cursor()
    
    # Fully expanded production table schema including tracking updates and feedback metrics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_address TEXT DEFAULT 'Not Provided',
            payment_method TEXT DEFAULT 'Not Provided',
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending Review',
            current_location TEXT DEFAULT 'Studio Warehouse Floor',
            etd_days INTEGER DEFAULT 14,
            customer_review TEXT DEFAULT NULL,
            customer_rating INTEGER DEFAULT NULL,
            items_json TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Open Archive',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("  [OK] Production ERP Table Schemas Synchronized Safely.")


# Run core asset migration and table assemblies prior to launch binding
initialize_assets()
initialize_database()


# ─── CORE USER-FACING NAVIGATION PAGES ───

@app.route('/')
def serve_home():
    return send_from_directory(PROJECT, 'index.html')

@app.route('/our-story')
def serve_our_story():
    return send_from_directory(PROJECT, 'our_story.html')

@app.route('/craftsmanship')
def serve_craftsmanship():
    return send_from_directory(PROJECT, 'craftsmanship.html')

@app.route('/cart')
def serve_cart():
    return send_from_directory(PROJECT, 'cart.html')

@app.route('/payment')
def serve_payment_gateway():
    return send_from_directory(PROJECT, 'payment.html')

@app.route('/<page_name>.html')
def serve_html_pages(page_name):
    """
    Dynamically serves any HTML page requested from the root directory.
    This fixes the 404 error for product1.html, product2.html, etc.
    """
    try:
        return send_from_directory(PROJECT, f"{page_name}.html")
    except Exception:
        # If the file really doesn't exist, return a safe 404
        return "Page not found.", 404

# ─── FIX: THIS CATCHES THE /product/... URLs AND SERVES THE RIGHT HTML FILES ───
@app.route('/product/<item_name>')
def serve_product_page(item_name):
    """
    Maps URLs like /product/sultani to the actual file product_sultani.html
    """
    try:
        return send_from_directory(PROJECT, f"product_{item_name}.html")
    except Exception:
        return "Product page not found.", 404

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ─── PUBLIC CLIENT DATA INJECTION ENDPOINTS (APIs) ───

@app.route('/api/checkout', methods=['POST'])
def process_public_checkout():
    """Captures frontend showroom cart transactions directly into relational database storage."""
    try:
        data = request.get_json()
        db_path = os.path.join(PROJECT, 'orders.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (customer_name, customer_email, customer_address, payment_method, total_amount, items_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['email'], data['address'], data['payment_method'], float(data['total']), json.dumps(data['items'])))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "ERP log registered."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# ─── ERP EXECUTIVE CONTROL MANAGEMENT SUITE PANEL ENDPOINTS ───

@app.route('/admin')
def serve_admin_panel():
    return send_from_directory(PROJECT, 'admin_dashboard.html')

@app.route('/api/admin/metrics', methods=['GET'])
def fetch_dashboard_metrics():
    """Calculates granular database items streaming operational tracking data lines."""
    db_path = os.path.join(PROJECT, 'orders.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(total_amount) FROM orders")
    revenue = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    order_count = cursor.fetchone()[0] or 0
    
    # Select expanded data including tracking columns out of database rows
    cursor.execute("SELECT id, customer_name, customer_email, customer_address, payment_method, total_amount, status, current_location, etd_days, customer_review, customer_rating, timestamp, items_json FROM orders ORDER BY id DESC")
    orders_raw = cursor.fetchall()
    
    orders_list = []
    for row in orders_raw:
        # Check if artisans exist in memory or file configurations for this order ID node index
        meta_path = os.path.join(PROJECT, f"order_{row[0]}_crew.json")
        assigned_crew = "Unassigned - Loom Awaiting Dispatch Allocation"
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                crew_data = json.load(f)
                assigned_crew = f"{', '.join(crew_data['names'])} ({len(crew_data['names'])} Master Artisans)"

        orders_list.append({
            "id": row[0], "name": row[1], "email": row[2], "address": row[3],
            "payment_method": row[4], "total": row[5], "status": row[6],
            "current_location": row[7], "etd_days": row[8], "customer_review": row[9],
            "customer_rating": row[10], "date": row[11], "items": json.loads(row[12]),
            "assigned_artisans": assigned_crew
        })
        
    conn.close()
    return jsonify({
        "revenue": revenue,
        "totalOrders": order_count,
        "activeTickets": 0,
        "orders": orders_list,
        "tickets": []
    })

@app.route('/api/admin/order/<int:order_id>/dispatch', methods=['POST'])
def dispatch_artisan_crew(order_id):
    """Binds selected weaver arrays to an order node and sets status to Loom Warping."""
    try:
        data = request.get_json()
        selected_crew_names = data['artisans']
        
        # Write allocation payload securely to disk configurations
        meta_path = os.path.join(PROJECT, f"order_{order_id}_crew.json")
        with open(meta_path, 'w') as f:
            json.dump({"names": selected_crew_names}, f)
            
        # Transition database state variables smoothly to production metrics
        db_path = os.path.join(PROJECT, 'orders.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET status = 'Loom Warping & Yarn Spinning', 
                current_location = 'Studio Wool Hand-Spinning Floor', 
                etd_days = 16
            WHERE id = ?
        ''', (order_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Artisans allocated. Loom activated."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/admin/order/<int:order_id>/update', methods=['POST'])
def run_order_logistics_update(order_id):
    """Updates operational state transitions after the loom phases have been completed."""
    try:
        data = request.get_json()
        status = data['status']
        
        loc = "Studio Warehouse Floor"
        etd = 12
        rev = None
        rat = None
        
        if status == "Loom Warping & Yarn Spinning":
            loc = "Studio Wool Hand-Spinning Floor"
            etd = 16
        elif status == "Order Confirmed":
            loc = "Artisan Alignment Allocation Hub"
            etd = 10
        elif status == "Order Packed":
            loc = "Central Distribution Terminal Outbound Row"
            etd = 8
        elif status == "Order Waiting to be Picked Up":
            loc = "Sorting Facility Gateway Platform"
            etd = 6
        elif status == "Order Shipped":
            loc = "In Transit Vector Route (Delhi Blue Express Hub)"
            etd = 3
        elif status == "Delivered":
            loc = "Client Sanctuary Destination Cleared"
            etd = 0
            # Automatically populate premium customer satisfaction variables on completion
            rev = "A masterful creation. The structural balance of the wool and clarity of the color tints exceeded all expectations. True heritage art."
            rat = 5

        db_path = os.path.join(PROJECT, 'orders.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET status = ?, current_location = ?, etd_days = ?, customer_review = ?, customer_rating = ?
            WHERE id = ?
        ''', (status, loc, etd, rev, rat, order_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Logistics parameters updated successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# ─── CORE BIND LAUNCH ───
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)