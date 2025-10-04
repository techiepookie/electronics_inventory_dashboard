import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="Electronics Inventory Manager", page_icon="🔧", layout="wide")

# Authentication
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        username = st.session_state["username"]
        password = st.session_state["password"]
        
        # Get credentials from environment variables
        valid_password = os.getenv("INVENTORY_PASSWORD")
        valid_username = os.getenv("INVENTORY_USERNAME")

        # Hash the entered password for comparison
        if username == valid_username and password == valid_password:
            st.session_state["password_correct"] = True
            st.session_state["logged_in_user"] = username
            del st.session_state["password"]  # Don't store password
            del st.session_state["username"]  # Don't store username
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated
    if st.session_state.get("password_correct", False):
        return True

    # Show login form
    st.markdown("### 🔐 Login to Electronics Inventory")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=password_entered)
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Invalid username or password")
    
    st.divider()
    st.info("💡 **Setup Instructions:**\n\n"
            "1. Create a `.env` file in the same folder as this app\n"
            "2. Add these lines:\n"
            "```\n"
            "INVENTORY_USERNAME=your_username\n"
            "INVENTORY_PASSWORD=your_password\n"
            "```\n"
            "3. Restart the app")
    
    return False

# Check authentication
if not check_password():
    st.stop()  # Don't continue if not authenticated

# Initialize DuckDB connection
@st.cache_resource
def init_db():
    conn = duckdb.connect('electronics_inventory.db')
    # Drop and recreate table with proper auto-increment
    try:
        conn.execute('DROP TABLE IF EXISTS inventory')
        conn.execute('DROP SEQUENCE IF EXISTS inventory_id_seq')
    except:
        pass
    
    conn.execute('CREATE SEQUENCE inventory_id_seq START 1')
    conn.execute('''
        CREATE TABLE inventory (
            id INTEGER DEFAULT nextval('inventory_id_seq'),
            category VARCHAR,
            item_name VARCHAR,
            quantity INTEGER,
            notes VARCHAR,
            price FLOAT,
            image_data BLOB,
            date_added TIMESTAMP,
            last_updated TIMESTAMP
        )
    ''')
    return conn

conn = init_db()

# Categories
CATEGORIES = [
    "Tools & Accessories",
    "Microcontrollers & Boards",
    "Display Modules",
    "Keypads & Buttons",
    "Sensors & Modules",
    "Motors & Drivers",
    "Power & Battery",
    "Integrated Circuits (ICs)",
    "Basic Components",
    "Boards & Prototyping",
    "Wires & Connectors",
    "Other"
]

# Helper functions
def image_to_bytes(image_file):
    """Convert uploaded image to bytes"""
    if image_file is not None:
        return image_file.read()
    return None

def bytes_to_image(image_bytes):
    """Convert bytes back to image"""
    if image_bytes:
        return Image.open(BytesIO(image_bytes))
    return None

def add_item(category, item_name, quantity, notes, price, image_bytes=None):
    now = datetime.now()
    conn.execute('''
        INSERT INTO inventory (category, item_name, quantity, notes, price, image_data, date_added, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [category, item_name, quantity, notes, price, image_bytes, now, now])

def update_item(item_id, quantity, notes, price, image_bytes=None):
    """Update item with optional new image"""
    if image_bytes is not None:
        conn.execute('''
            UPDATE inventory 
            SET quantity = ?, notes = ?, price = ?, image_data = ?, last_updated = ?
            WHERE id = ?
        ''', [quantity, notes, price, image_bytes, datetime.now(), item_id])
    else:
        conn.execute('''
            UPDATE inventory 
            SET quantity = ?, notes = ?, price = ?, last_updated = ?
            WHERE id = ?
        ''', [quantity, notes, price, datetime.now(), item_id])

def delete_item(item_id):
    conn.execute('DELETE FROM inventory WHERE id = ?', [item_id])

def get_all_items():
    return conn.execute('SELECT id, category, item_name, quantity, notes, price, date_added, last_updated FROM inventory ORDER BY category, item_name').df()

def get_item_with_image(item_id):
    result = conn.execute('SELECT * FROM inventory WHERE id = ?', [item_id]).fetchone()
    return result

def search_items(query):
    return conn.execute('''
        SELECT id, category, item_name, quantity, notes, price, date_added, last_updated
        FROM inventory 
        WHERE item_name ILIKE ? OR notes ILIKE ? OR category ILIKE ?
        ORDER BY category, item_name
    ''', [f'%{query}%', f'%{query}%', f'%{query}%']).df()

def get_stats():
    total = conn.execute('SELECT COUNT(*) as count FROM inventory').fetchone()[0]
    by_category = conn.execute('''
        SELECT category, COUNT(*) as count, SUM(quantity) as total_qty
        FROM inventory 
        GROUP BY category 
        ORDER BY count DESC
    ''').df()
    return total, by_category

# Sidebar
st.sidebar.title("🔧 Electronics Inventory")
st.sidebar.write(f"👤 Logged in as: **{st.session_state.get('logged_in_user', 'User')}**")

if st.sidebar.button("🚪 Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.divider()

menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "➕ Add Item", "🔍 Search & Manage", "📥 Bulk Import"])

# Dashboard
if menu == "📊 Dashboard":
    st.title("📊 Inventory Dashboard")
    
    total_items, category_stats = get_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Items", total_items)
    with col2:
        st.metric("Categories", len(category_stats))
    with col3:
        total_qty = category_stats['total_qty'].sum() if not category_stats.empty else 0
        st.metric("Total Quantity", int(total_qty))
    
    st.subheader("📦 Items by Category")
    if not category_stats.empty:
        st.dataframe(category_stats, use_container_width=True, hide_index=True)
    else:
        st.info("No items in inventory yet. Add some items to get started!")
    
    st.subheader("🗂️ All Items")
    df = get_all_items()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Your inventory is empty. Start adding items!")

# Add Item
elif menu == "➕ Add Item":
    st.title("➕ Add New Item")
    
    with st.form("add_item_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox("Category", CATEGORIES)
            item_name = st.text_input("Item Name")
            quantity = st.number_input("Quantity", min_value=1, value=1)
            price = st.number_input("Price (₹)", min_value=0.0, value=0.0, step=10.0)
        
        with col2:
            notes = st.text_area("Notes/Specifications", height=100)
            image_file = st.file_uploader("Upload Image (optional)", type=['png', 'jpg', 'jpeg', 'webp'])
            
            if image_file:
                st.image(image_file, caption="Preview", width=200)
        
        submit = st.form_submit_button("Add Item")
        
        if submit:
            if item_name:
                image_bytes = image_to_bytes(image_file) if image_file else None
                add_item(category, item_name, quantity, notes, price, image_bytes)
                st.success(f"✅ Added {item_name} to inventory!")
                st.rerun()
            else:
                st.error("Please enter an item name")

# Search & Manage
elif menu == "🔍 Search & Manage":
    st.title("🔍 Search & Manage Items")
    
    search_query = st.text_input("🔎 Search by name, category, or notes", "")
    
    if search_query:
        df = search_items(search_query)
        st.write(f"Found {len(df)} items")
    else:
        df = get_all_items()
    
    if not df.empty:
        for idx, row in df.iterrows():
            with st.expander(f"**{row['item_name']}** ({row['category']}) - Qty: {row['quantity']}"):
                # Get full item data including image
                item_data = get_item_with_image(row['id'])
                
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    # Display image if available
                    if item_data[6]:  # image_data is at index 6
                        img = bytes_to_image(item_data[6])
                        st.image(img, width=200)
                    else:
                        st.info("No image uploaded")
                    
                    st.write(f"**Notes:** {row['notes']}")
                    st.write(f"**Price:** ₹{row['price']}")
                    st.write(f"**Added:** {row['date_added']}")
                
                with col2:
                    with st.form(key=f"update_form_{row['id']}"):
                        new_qty = st.number_input("Quantity", min_value=0, value=int(row['quantity']), key=f"qty_{row['id']}")
                        new_notes = st.text_area("Notes", value=row['notes'], key=f"notes_{row['id']}")
                        new_price = st.number_input("Price (₹)", min_value=0.0, value=float(row['price']), key=f"price_{row['id']}")
                        new_image = st.file_uploader("Update Image", type=['png', 'jpg', 'jpeg', 'webp'], key=f"img_{row['id']}")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.form_submit_button("💾 Update", use_container_width=True):
                                image_bytes = image_to_bytes(new_image) if new_image else None
                                update_item(row['id'], new_qty, new_notes, new_price, image_bytes)
                                st.success("Updated!")
                                st.rerun()
                        
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{row['id']}", type="secondary", use_container_width=True):
                        delete_item(row['id'])
                        st.success("Deleted!")
                        st.rerun()
    else:
        st.info("No items found")


# Footer
st.sidebar.divider()
st.sidebar.info("💡 **Tip:** Add images to easily identify components!")
st.sidebar.caption("Built with Streamlit & DuckDB")