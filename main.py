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
        valid_username = os.getenv("INVENTORY_USERNAME", "admin")
        valid_password = os.getenv("INVENTORY_PASSWORD", "admin123")
        
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

# Bulk Import
elif menu == "📥 Bulk Import":
    st.title("📥 Bulk Import Items")
    st.write("Import your existing inventory from your parts list")
    
    st.warning("⚠️ Note: Bulk imported items won't have images initially. You can add images later from the Search & Manage page.")
    
    if st.button("Import NEW PARTS LIST"):
        # Tools & Accessories
        add_item("Tools & Accessories", "Multitec MT-07 Nipper", 1, "Wire nipper for smooth cutting", 0)
        add_item("Tools & Accessories", "150B Canon Wire Stripper & Cutter", 1, "Sharp wire cutter", 0)
        add_item("Tools & Accessories", "10K Potentiometer with Knob", 1, "Adjustable resistor for voltage control", 0)
        add_item("Tools & Accessories", "USB Type A to B Cable (20cm)", 1, "For Arduino connection", 0)
        add_item("Tools & Accessories", "Arduino UNO R3 Transparent Plastic Case", 1, "Protection case for Arduino", 0)
        
        # Microcontrollers
        add_item("Microcontrollers & Boards", "Raspberry Pi Pico", 1, "Microcontroller board", 0)
        add_item("Microcontrollers & Boards", "Arduino UNO R3 SMD ATmega328", 1, "Compatible Arduino Board", 0)
        add_item("Microcontrollers & Boards", "NodeMCU ESP8266 V3 (LOLIN CH340)", 1, "WiFi-enabled microcontroller board", 0)
        
        # Display Modules
        add_item("Display Modules", "16x2 LCD Display (Blue)", 1, "For microcontroller projects", 0)
        add_item("Display Modules", "7-Segment LED Display (Common Cathode)", 4, "For numerical output", 0)
        
        # Keypads & Buttons
        add_item("Keypads & Buttons", "4x3 Flexible Matrix Keypad", 1, "Membrane keypad", 0)
        add_item("Keypads & Buttons", "Matrix 16 Button Keypad Module (4x4)", 1, "Multi-key module", 0)
        add_item("Keypads & Buttons", "TTP229 16-Channel Capacitive Touch Module", 1, "Multi-touch sensor", 0)
        add_item("Keypads & Buttons", "4-Pins DIP Momentary Tactile Push Button 6x6x8mm", 10, "10 pcs pack", 0)
        add_item("Keypads & Buttons", "4-Pins DIP Momentary Tactile Push Button 6x6x5mm", 10, "10 pcs pack", 0)
        add_item("Keypads & Buttons", "Red PBS-11B 2PIN 12mm No Lock Push Button", 1, "3A, 250V", 0)
        add_item("Keypads & Buttons", "2 Pin Button Switch (Pack of 10)", 10, "Compact mini switch", 0)
        
        # Sensors & Modules
        add_item("Sensors & Modules", "PS2 Joystick Module Breakout Sensor", 3, "For gaming projects", 0)
        add_item("Sensors & Modules", "MQ-5 Gas Sensor Module", 1, "Detect H2, LPG, CH4, CO", 0)
        add_item("Sensors & Modules", "Microwave Radar Human Body Sensor", 1, "Motion sensor", 0)
        add_item("Sensors & Modules", "Condenser Microphone", 1, "High sensitivity", 0)
        add_item("Sensors & Modules", "Micro SD Card Adapter", 1, "For SD storage", 0)
        add_item("Sensors & Modules", "Mini DF MP3 Player Module MP3-TF-16P", 1, "Audio playback module", 0)
        add_item("Sensors & Modules", "Coin Type Micro Vibration Motor", 1, "Haptic feedback", 0)
        
        # Motors & Drivers
        add_item("Motors & Drivers", "L293D Motor Driver IC", 1, "H-bridge motor control", 0)
        add_item("Motors & Drivers", "A4988 Stepper Motor Driver with Heat Sink", 1, "For stepper motors", 0)
        
        # Power & Battery
        add_item("Power & Battery", "1S 18650 Li-ion Battery BMS Charger Protection Board", 1, "3.7V battery protection", 0)
        
        # Integrated Circuits
        add_item("Integrated Circuits (ICs)", "CD4028 BCD to Decimal Decoder IC", 1, "Digital display decoding", 0)
        add_item("Integrated Circuits (ICs)", "74LS125 Quad Tri-State Buffer IC", 1, "DIP-14 package", 0)
        add_item("Integrated Circuits (ICs)", "CD4071 Quad 2-input OR Gate", 1, "Digital logic", 0)
        add_item("Integrated Circuits (ICs)", "CD4049 Hex Inverting Buffer IC", 1, "Digital signal processing", 0)
        add_item("Integrated Circuits (ICs)", "CD4001 Quad 2-Input NOR Gate IC", 1, "Digital logic", 0)
        add_item("Integrated Circuits (ICs)", "CD4066 Quad Bilateral Switch IC", 1, "Analog/Digital switching", 0)
        add_item("Integrated Circuits (ICs)", "CD4070 Quad 2-Input XOR Gate IC", 1, "Logic circuits", 0)
        add_item("Integrated Circuits (ICs)", "CD4511 BCD to 7 Segment Latch Decoder Driver IC", 1, "Digital display driver", 0)
        add_item("Integrated Circuits (ICs)", "555 Timer IC", 2, "Pulse generation & timing", 0)
        
        # Basic Components
        add_item("Basic Components", "BC547 Transistor (Pack of 5)", 5, "NPN low-power", 0)
        add_item("Basic Components", "BC548 NPN Transistor (Pack of 5)", 5, "Switching & amplifier", 0)
        add_item("Basic Components", "BC558 PNP Transistor (Pack of 5)", 5, "Switching & amplifier", 0)
        add_item("Basic Components", "Ceramic Capacitor Box (100 pcs)", 100, "Assorted values (10nF–100nF typical)", 0)
        add_item("Basic Components", "1x40 2.54mm Pitch Female Berg Strip Header (Right Angle)", 4, "PCB connector", 0)
        
        # Boards & Prototyping
        add_item("Boards & Prototyping", "MB102 830 Points Solderless Breadboard", 1, "For Arduino projects", 0)
        add_item("Boards & Prototyping", "170 Points Mini Breadboard", 2, "Small solderless breadboard", 0)
        
        # Wires & Connectors
        add_item("Wires & Connectors", "Female to Female Jumper Wires (20cm, 40 pcs)", 40, "For breadboard connections", 0)
        add_item("Wires & Connectors", "Male to Female Jumper Wires (20cm, 40 pcs)", 40, "For breadboard connections", 0)
        
        st.success("✅ Imported NEW PARTS LIST successfully!")
        st.rerun()
    
    st.divider()
    
    if st.button("Import OLD PARTS LIST"):
        add_item("Microcontrollers & Boards", "ESP32 Development Board", 1, "Microcontroller", 400)
        add_item("Power & Battery", "18650 Li-ion Battery", 1, "3.7V", 250)
        add_item("Other", "Drone Propellers", 1, "Pair, 5 inch approx", 250)
        add_item("Sensors & Modules", "TTP223 Capacitive Touch Module", 1, "16-channel", 125)
        add_item("Wires & Connectors", "Jumper Wires (assorted)", 40, "40 pcs", 35)
        add_item("Power & Battery", "5V 2A SMPS / Power Supply", 1, "Bench supply", 360)
        add_item("Other", "Frame Materials & Wires", 1, "For DIY projects", 200)
        
        st.success("✅ Imported OLD PARTS LIST successfully!")
        st.rerun()

# Footer
st.sidebar.divider()
st.sidebar.info("💡 **Tip:** Add images to easily identify components!")
st.sidebar.caption("Built with Streamlit & DuckDB")