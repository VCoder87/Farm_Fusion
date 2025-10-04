from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import bcrypt
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

app = Flask(__name__)
app.config.from_object('config.Config')

# MySQL configuration
import mysql.connector
from mysql.connector import Error

# Database connection function using mysql.connector (this works!)
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            port=app.config.get('MYSQL_PORT', 3306)
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

# Allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            print("=== Registration Debug ===")
            print(f"MySQL object: {mysql}")
            print(f"Has connection attr: {hasattr(mysql, 'connection')}")
            
            if hasattr(mysql, 'connection'):
                print(f"Connection value: {mysql.connection}")
            
            # Try to get connection
            conn = get_db_connection()
            print(f"Got connection: {conn}")
            
            if conn is None:
                flash('Database connection is None. Check if MySQL server is running.')
                return redirect(url_for('register'))
            
            # Get form data - matching your HTML form fields
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            first_name = request.form.get('first_name', '')
            last_name = request.form.get('last_name', '')
            phone = request.form.get('phone', '')
            location = request.form.get('location', '')
            user_type = request.form.get('user_type', '')
            
            # Validate password confirmation
            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('register'))
            
            # Combine first and last name
            full_name = f"{first_name} {last_name}".strip()
            
            password_hash = generate_password_hash(password)
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, phone, location, user_type) 
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (username, email, password_hash, full_name, phone, location, user_type))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Registration successful!')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            flash(f'Registration failed: {str(e)}')
            return redirect(url_for('register'))
    
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password_hash, full_name FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()  
            
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['full_name'] = user[3]
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password!', 'error')
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
    
    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        if conn is None:
            flash('Database connection failed.', 'error')
            return redirect(url_for('login'))
            
        cursor = conn.cursor()
        
        # Get user's equipment rentals with proper column mapping
        cursor.execute("""
            SELECT id, equipment_name as name, description, category, rental_price_per_day as daily_rate, 
                   availability_status, created_at, location, image_url
            FROM equipment_rentals 
            WHERE owner_id = %s
            ORDER BY created_at DESC
        """, (session['user_id'],))
        
        equipment_results = cursor.fetchall()
        
        # Convert to list of dictionaries for easier template access
        my_equipment = []
        for eq in equipment_results:
            my_equipment.append({
                'id': eq[0],
                'name': eq[1],
                'description': eq[2],
                'category': eq[3],
                'daily_rate': eq[4],
                'availability_status': eq[5],
                'created_at': eq[6],
                'location': eq[7],
                'image_url': eq[8]
            })
        
        # Get user's marketplace items with proper column mapping
        cursor.execute("""
            SELECT id, item_name as name, description, category, price, quantity_available, 
                   unit, created_at, location, image_url
            FROM marketplace_items 
            WHERE seller_id = %s
            ORDER BY created_at DESC
        """, (session['user_id'],))
        
        products_results = cursor.fetchall()
        
        # Convert to list of dictionaries for easier template access
        my_products = []
        for prod in products_results:
            my_products.append({
                'id': prod[0],
                'name': prod[1],
                'description': prod[2],
                'category': prod[3],
                'price': prod[4],
                'quantity_available': prod[5],
                'unit': prod[6],
                'created_at': prod[7],
                'location': prod[8],
                'image_url': prod[9]
            })
        
        # Calculate counts for dashboard cards
        equipment_count = len(my_equipment)
        products_count = len(my_products)
        
        # Get active rentals count (equipment currently rented out)
        cursor.execute("""
            SELECT COUNT(*) FROM rental_transactions rt
            JOIN equipment_rentals er ON rt.equipment_id = er.id
            WHERE er.owner_id = %s AND rt.rental_end_date >= CURDATE()
        """, (session['user_id'],))
        active_rentals_result = cursor.fetchone()
        active_rentals = active_rentals_result[0] if active_rentals_result else 0
        
        # Get recent orders count (purchases made this month)
        cursor.execute("""
            SELECT COUNT(*) FROM purchase_transactions pt
            WHERE pt.buyer_id = %s AND MONTH(pt.created_at) = MONTH(CURDATE()) 
            AND YEAR(pt.created_at) = YEAR(CURDATE())
        """, (session['user_id'],))
        recent_orders_result = cursor.fetchone()
        recent_orders = recent_orders_result[0] if recent_orders_result else 0
        
        cursor.close()
        conn.close()
        
        # Get user data from session
        current_user = {
            'id': session['user_id'],
            'username': session['username'],
            'first_name': session['full_name'].split()[0] if session['full_name'] else session['username']
        }
        
        return render_template('dashboard.html', 
                             current_user=current_user,
                             my_equipment=my_equipment,
                             my_products=my_products,
                             equipment_count=equipment_count,
                             products_count=products_count,
                             active_rentals=active_rentals,
                             recent_orders=recent_orders)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        
        # Return empty data if there's an error
        current_user = {
            'id': session.get('user_id', 0),
            'username': session.get('username', 'User'),
            'first_name': session.get('full_name', 'User').split()[0] if session.get('full_name') else 'User'
        }
        
        return render_template('dashboard.html', 
                             current_user=current_user,
                             my_equipment=[],
                             my_products=[],
                             equipment_count=0,
                             products_count=0,
                             active_rentals=0,
                             recent_orders=0)
# Replace your existing rent_equipment route with this corrected version:

@app.route('/rent_equipment', methods=['GET', 'POST'])
def rent_equipment():
    """Handle equipment rental listing - ADD equipment (form submission)"""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            equipment_name = request.form.get('equipment_name')
            description = request.form.get('description')
            category = request.form.get('category')
            rental_price_per_day = request.form.get('rental_price_per_day')
            location = request.form.get('location')
            rental_price_per_week = request.form.get('rental_price_per_week', '0')
            rental_price_per_month = request.form.get('rental_price_per_month', '0')
            
            # Validate required fields
            if not all([equipment_name, description, category, rental_price_per_day, location]):
                flash('Please fill in all required fields.', 'error')
                return redirect(url_for('rent_equipment'))
            
            # Convert prices to float
            try:
                rental_price_per_day = float(rental_price_per_day)
                rental_price_per_week = float(rental_price_per_week) if rental_price_per_week else 0
                rental_price_per_month = float(rental_price_per_month) if rental_price_per_month else 0
            except ValueError:
                flash('Please enter valid prices.', 'error')
                return redirect(url_for('rent_equipment'))
            
            # Handle image upload
            image_url = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Generate unique filename
                    filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    image_url = filename
            
            # Save to database
            conn = get_db_connection()
            if conn is None:
                flash('Database connection failed. Please try again.', 'error')
                return redirect(url_for('rent_equipment'))
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO equipment_rentals 
                (owner_id, equipment_name, description, category, rental_price_per_day, 
                 rental_price_per_week, rental_price_per_month, location, image_url, availability_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], equipment_name, description, category, 
                  rental_price_per_day, rental_price_per_week, rental_price_per_month, 
                  location, image_url, 'available'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Equipment listed successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Error in rent_equipment POST: {e}")
            flash(f'Error listing equipment: {str(e)}', 'error')
            return redirect(url_for('rent_equipment'))
    
    # GET request - show the form to ADD equipment
    return render_template('rent_equipment.html')


# Also, make sure you have proper configuration for file uploads
# Add these to your app configuration if not already present:
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
@app.route('/rent_listings')
def rent_listings():
    """Redirect to browse_equipment for consistency"""
    return redirect(url_for('browse_equipment'))

@app.route('/buy_items')
def buy_items():
    """Browse items available for purchase"""
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get search parameters
        search_term = request.args.get('search', '')
        category = request.args.get('category', '')
        location = request.args.get('location', '')
        
        # Build query with search filters
        base_query = """
            SELECT m.id, m.item_name, m.description, m.category, m.price, m.quantity_available,
                   m.unit, m.location, m.image_url, u.full_name, u.phone
            FROM marketplace_items m
            JOIN users u ON m.seller_id = u.id
            WHERE m.quantity_available > 0
        """
        
        params = []
        
        if search_term:
            base_query += " AND (m.item_name LIKE %s OR m.description LIKE %s)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        if category and category != '':
            base_query += " AND m.category = %s"
            params.append(category)
        
        if location:
            base_query += " AND m.location LIKE %s"
            params.append(f'%{location}%')
        
        base_query += " ORDER BY m.created_at DESC"
        
        cursor.execute(base_query, params)
        items = cursor.fetchall()
        
        # Convert to list of dictionaries to match template expectations
        products = []
        for item in items:
            products.append({
                'id': item[0],
                'name': item[1],  # item_name -> name
                'description': item[2],
                'category': item[3],
                'price': item[4],
                'quantity_available': item[5],
                'unit': item[6],
                'location': item[7],
                'image_url': f"/static/uploads/{item[8]}" if item[8] else None,
                'seller_name': item[9],
                'seller_phone': item[10],
                'status': 'active'  # Add status field expected by template
            })
        
        cursor.close()
        conn.close()
        
        # Pass 'products' to match template expectations
        return render_template('buy_items.html', products=products)
        
    except Exception as e:
        print(f"Error in buy_items: {e}")
        flash(f'Error loading items: {str(e)}', 'error')
        return render_template('buy_items.html', products=[])

# Also add a POST route to handle purchases
@app.route('/buy_items', methods=['POST'])
def process_purchase():
    """Handle product purchase"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        delivery_address = request.form.get('delivery_address')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get item details
        cursor.execute("""
            SELECT seller_id, price, quantity_available, item_name FROM marketplace_items WHERE id = %s
        """, (product_id,))
        item = cursor.fetchone()
        
        if item and item[2] >= quantity:
            seller_id = item[0]
            price = item[1]
            item_name = item[3]
            total_amount = quantity * price
            
            # Create purchase transaction
            cursor.execute("""
                INSERT INTO purchase_transactions 
                (item_id, buyer_id, seller_id, quantity, total_amount, delivery_address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (product_id, session['user_id'], seller_id, quantity, total_amount, delivery_address))
            
            # Update item quantity
            cursor.execute("""
                UPDATE marketplace_items SET quantity_available = quantity_available - %s
                WHERE id = %s
            """, (quantity, product_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': f'Successfully purchased {quantity} units of {item_name}'})
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Insufficient quantity available'})
            
    except Exception as e:
        print(f"Purchase error: {e}")
        return jsonify({'success': False, 'message': f'Purchase failed: {str(e)}'})
# NEW: Sell Item Route
# Add this validation to your sell_item route, before the database insert:

@app.route('/sell_item', methods=['GET', 'POST'])
def sell_item():
    if 'user_id' not in session:
        flash('Please log in to sell items.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            item_name = request.form['item_name']
            description = request.form['description']
            category = request.form['category']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            unit = request.form['unit']
            location = request.form['location']
            
            # ADD THIS VALIDATION - Check category length
            if len(category) > 10:  # Adjust this number based on your actual column size
                flash('Category name is too long. Please choose a different category.', 'error')
                return redirect(url_for('sell_item'))
            
            # Map long category names to shorter ones (temporary fix)
            category_mapping = {
                'Grains': 'Grain',
                'Vegetables': 'Veg',
                'Fruits': 'Fruit',
                'Dairy': 'Dairy',
                'Spices': 'Spice',
                'Seeds': 'Seed'
            }
            
            if category in category_mapping:
                category = category_mapping[category]
            
            # Rest of your existing code...
            # Handle image upload
            image_url = None
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    image_url = filename
            
            # Save to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO marketplace_items 
                (seller_id, item_name, description, category, price, quantity_available, unit, location, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], item_name, description, category, price, quantity, unit, location, image_url))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Item listed for sale successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error listing item: {str(e)}', 'error')
            return redirect(url_for('sell_item'))
    
    # GET request - show the sell item form
    return render_template('sell_item.html')
# NEW: My Listings Route
@app.route('/my_listings')
def my_listings():
    """View current user's marketplace listings"""
    if 'user_id' not in session:
        flash('Please log in to view your listings.', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, item_name, description, category, price, quantity_available, 
                   unit, location, image_url, created_at
            FROM marketplace_items 
            WHERE seller_id = %s
            ORDER BY created_at DESC
        """, (session['user_id'],))
        
        listings = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('my_listings.html', listings=listings)
        
    except Exception as e:
        flash(f'Error loading your listings: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# NEW: Edit Listing Route
@app.route('/edit_listing/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(listing_id):
    """Edit a marketplace listing"""
    if 'user_id' not in session:
        flash('Please log in to edit listings.', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the listing belongs to the current user
    cursor.execute("""
        SELECT * FROM marketplace_items 
        WHERE id = %s AND seller_id = %s
    """, (listing_id, session['user_id']))
    
    listing = cursor.fetchone()
    
    if not listing:
        flash('Listing not found or you do not have permission to edit it.', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('my_listings'))
    
    if request.method == 'POST':
        try:
            # Get form data
            item_name = request.form['item_name']
            description = request.form['description']
            category = request.form['category']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            unit = request.form['unit']
            location = request.form['location']
            
            # Handle image upload (optional - keep existing if no new image)
            image_url = listing[9]  # Keep existing image by default
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    image_url = filename
            
            # Update database
            cursor.execute("""
                UPDATE marketplace_items 
                SET item_name = %s, description = %s, category = %s, price = %s, 
                    quantity_available = %s, unit = %s, location = %s, image_url = %s
                WHERE id = %s AND seller_id = %s
            """, (item_name, description, category, price, quantity, unit, location, 
                  image_url, listing_id, session['user_id']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Listing updated successfully!', 'success')
            return redirect(url_for('my_listings'))
            
        except Exception as e:
            flash(f'Error updating listing: {str(e)}', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('edit_listing', listing_id=listing_id))
    
    cursor.close()
    conn.close()
    
    return render_template('edit_listing.html', listing=listing)

# NEW: Delete Listing Route
@app.route('/delete_listing/<int:listing_id>', methods=['POST'])
def delete_listing(listing_id):
    """Delete a marketplace listing"""
    if 'user_id' not in session:
        flash('Please log in to delete listings.', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the listing belongs to the current user
        cursor.execute("""
            DELETE FROM marketplace_items 
            WHERE id = %s AND seller_id = %s
        """, (listing_id, session['user_id']))
        
        if cursor.rowcount > 0:
            conn.commit()
            flash('Listing deleted successfully!', 'success')
        else:
            flash('Listing not found or you do not have permission to delete it.', 'error')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        flash(f'Error deleting listing: {str(e)}', 'error')
    
    return redirect(url_for('my_listings'))

# Equipment Rental Routes


# View all equipment for rent
@app.route('/browse_equipment')
def browse_equipment():
    """Browse equipment available for rent - SHOW equipment list"""
    if 'user_id' not in session:
        flash('Please log in to browse equipment.', 'error')
        return redirect(url_for('login'))
    
    print("=== DEBUG: browse_equipment route called ===")
    
    try:
        conn = get_db_connection()
        if conn is None:
            print("Database connection failed")
            flash('Database connection failed.', 'error')
            return render_template('rent_listings.html', listings=[])
        
        cursor = conn.cursor()
        
        # Get search parameters
        search_term = request.args.get('search', '')
        category = request.args.get('category', '')
        location = request.args.get('location', '')
        
        print(f"Search params - term: {search_term}, category: {category}, location: {location}")
        
        # Build query with search filters
        base_query = """
            SELECT e.id, e.equipment_name, e.description, e.category, e.rental_price_per_day,
                   e.rental_price_per_week, e.rental_price_per_month, e.location, e.image_url, 
                   u.full_name, u.phone, e.availability_status, e.created_at
            FROM equipment_rentals e
            JOIN users u ON e.owner_id = u.id
            WHERE e.availability_status = 'available'
        """
        
        params = []
        
        if search_term:
            base_query += " AND (e.equipment_name LIKE %s OR e.description LIKE %s)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        if category and category != 'all':
            base_query += " AND e.category = %s"
            params.append(category)
        
        if location:
            base_query += " AND e.location LIKE %s"
            params.append(f'%{location}%')
        
        base_query += " ORDER BY e.created_at DESC"
        
        print(f"Executing query: {base_query}")
        print(f"With params: {params}")
        
        cursor.execute(base_query, params)
        equipment = cursor.fetchall()
        
        print(f"Found {len(equipment)} equipment items")
        
        # Debug: Print first few items
        for i, item in enumerate(equipment[:3]):
            print(f"Equipment {i+1}: {item}")
        
        cursor.close()
        conn.close()
        
        return render_template('rent_listings.html', listings=equipment)
        
    except Exception as e:
        print(f"Error in browse_equipment: {e}")
        flash(f'Error loading equipment: {str(e)}', 'error')
        return render_template('rent_listings.html', listings=[])

@app.route('/search_equipment', methods=['POST'])
def search_equipment():
    """Handle equipment search"""
    search_term = request.form.get('search', '')
    category = request.form.get('category', '')
    location = request.form.get('location', '')
    
    # Redirect to browse with search parameters
    return redirect(url_for('browse_equipment', search=search_term, category=category, location=location))
@app.route('/my_equipment')
def my_equipment():
    """View current user's equipment listings"""
    if 'user_id' not in session:
        flash('Please log in to view your equipment.', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, equipment_name, description, category, rental_price_per_day, 
                   rental_price_per_week, rental_price_per_month, location, image_url, 
                   availability_status, created_at
            FROM equipment_rentals 
            WHERE owner_id = %s
            ORDER BY created_at DESC
        """, (session['user_id'],))
        
        equipment = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('my_equipment.html', equipment=equipment)
        
    except Exception as e:
        flash(f'Error loading your equipment: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Fix 4: Debug route to check if data exists
@app.route('/debug/equipment')
def debug_equipment():
    """Debug route to check equipment data"""
    if 'user_id' not in session:
        return "Please log in first"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check total equipment count
        cursor.execute("SELECT COUNT(*) FROM equipment_rentals")
        total_count = cursor.fetchone()[0]
        
        # Check available equipment count
        cursor.execute("SELECT COUNT(*) FROM equipment_rentals WHERE availability_status = 'available'")
        available_count = cursor.fetchone()[0]
        
        # Get sample data
        cursor.execute("SELECT id, equipment_name, owner_id, availability_status FROM equipment_rentals LIMIT 5")
        sample_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return f"""
        <h2>Equipment Debug Info</h2>
        <p>Total Equipment: {total_count}</p>
        <p>Available Equipment: {available_count}</p>
        <p>Sample Data: {sample_data}</p>
        """
        
    except Exception as e:
        return f"Error: {str(e)}"

# Fix 5: Add a route to seed some test data
@app.route('/debug/seed_equipment')
def seed_equipment():
    """Add some test equipment data"""
    if 'user_id' not in session:
        return "Please log in first"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Add test equipment
        test_equipment = [
            ('Tractor', 'Heavy duty farming tractor', 'Machinery', 500.0, 3000.0, 10000.0, 'Kochi', 'available'),
            ('Harvester', 'Combine harvester for grains', 'Machinery', 800.0, 4500.0, 15000.0, 'Ernakulam', 'available'),
            ('Plow', 'Steel plow for soil preparation', 'Tools', 100.0, 600.0, 2000.0, 'Thrissur', 'available'),
        ]
        
        for equipment in test_equipment:
            cursor.execute("""
                INSERT INTO equipment_rentals 
                (owner_id, equipment_name, description, category, rental_price_per_day, 
                 rental_price_per_week, rental_price_per_month, location, availability_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], *equipment))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return "Test equipment added successfully!"
        
    except Exception as e:
        return f"Error: {str(e)}"
# Marketplace Routes
@app.route('/marketplace/add', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        item_name = request.form['item_name']
        description = request.form['description']
        category = request.form['category']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        unit = request.form['unit']
        location = request.form['location']
        
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = filename
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO marketplace_items 
            (seller_id, item_name, description, category, price, quantity_available, unit, location, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], item_name, description, category, price, quantity, unit, location, image_url))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash('Item added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('buy_items.html')

# View marketplace
@app.route('/marketplace')
def marketplace():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.id, m.item_name, m.description, m.category, m.price, m.quantity_available,
               m.unit, m.location, m.image_url, u.full_name, u.phone
        FROM marketplace_items m
        JOIN users u ON m.seller_id = u.id
        WHERE m.quantity_available > 0
        ORDER BY m.created_at DESC
    """)
    items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('marketplace.html', items=items)

# Rent equipment
@app.route('/rent/request/<int:equipment_id>', methods=['POST'])
def request_rental(equipment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get equipment details
    cursor.execute("""
        SELECT owner_id, rental_price_per_day FROM equipment_rentals WHERE id = %s
    """, (equipment_id,))
    equipment = cursor.fetchone()
    
    if equipment:
        owner_id = equipment[0]
        daily_rate = equipment[1]
        
        # Calculate total amount
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days + 1
        total_amount = days * daily_rate
        
        cursor.execute("""
            INSERT INTO rental_transactions 
            (equipment_id, renter_id, owner_id, rental_start_date, rental_end_date, total_amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (equipment_id, session['user_id'], owner_id, start_date, end_date, total_amount))
        conn.commit()
        
        flash('Rental request submitted successfully!', 'success')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('browse_equipment'))

# Purchase item
@app.route('/buy/<int:item_id>', methods=['POST'])
def purchase_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    quantity = int(request.form['quantity'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get item details
    cursor.execute("""
        SELECT seller_id, price, quantity_available FROM marketplace_items WHERE id = %s
    """, (item_id,))
    item = cursor.fetchone()
    
    if item and item[2] >= quantity:
        seller_id = item[0]
        price = item[1]
        total_amount = quantity * price
        
        # Create purchase transaction
        cursor.execute("""
            INSERT INTO purchase_transactions 
            (item_id, buyer_id, seller_id, quantity, total_amount)
            VALUES (%s, %s, %s, %s, %s)
        """, (item_id, session['user_id'], seller_id, quantity, total_amount))
        
        # Update item quantity
        cursor.execute("""
            UPDATE marketplace_items SET quantity_available = quantity_available - %s
            WHERE id = %s
        """, (quantity, item_id))
        
        conn.commit()
        flash('Purchase successful!', 'success')
    else:
        flash('Insufficient quantity available!', 'error')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('marketplace'))

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True,port=5010)