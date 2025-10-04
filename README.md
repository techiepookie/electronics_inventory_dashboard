# 🔧 Electronics Inventory Manager

A powerful, easy-to-use inventory management system for electronics hobbyists and makers. Built with Streamlit and DuckDB for fast, efficient component tracking.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🔐 **Secure Login** - Password-protected access using environment variables
- 📊 **Dashboard** - Visual overview of your entire inventory
- ➕ **Add Items** - Quick form to add new components
- 🔍 **Smart Search** - Search across names, categories, and notes
- 📦 **Category Management** - Organize by component type
- 📥 **Bulk Import** - Import existing parts lists with one click
- 💾 **Persistent Storage** - DuckDB database for reliable data storage
- 🎯 **Quantity Tracking** - Update stock levels easily
- 💰 **Price Tracking** - Keep track of component costs

## 📋 Supported Categories

- Tools & Accessories
- Microcontrollers & Boards
- Display Modules
- Keypads & Buttons
- Sensors & Modules
- Motors & Drivers
- Power & Battery
- Integrated Circuits (ICs)
- Basic Components
- Boards & Prototyping
- Wires & Connectors
- Other

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root directory
   ```bash
   touch .env
   ```

4. **Add your credentials to `.env`**
   ```env
   INVENTORY_USERNAME=your_username
   INVENTORY_PASSWORD=your_secure_password
   ```

5. **Run the application**
   ```bash
   streamlit run inventory_app.py
   ```

6. **Access the app** in your browser (usually opens automatically at `http://localhost:8501`)

## 🔐 Security Setup

### Creating Secure Credentials

1. Create a `.env` file in the same directory as `inventory_app.py`
2. Add the following lines (replace with your own credentials):
   ```env
   INVENTORY_USERNAME=admin
   INVENTORY_PASSWORD=MySecurePassword123!
   ```

### Important Security Notes

- ⚠️ **Never commit your `.env` file to version control**
- ✅ Add `.env` to your `.gitignore` file
- 🔒 Use strong, unique passwords
- 📝 Keep a backup of your credentials in a secure location

### Default Credentials

If no `.env` file is found, the app uses these defaults:
- Username: `admin`
- Password: `admin123`

**⚠️ Change these immediately by creating your `.env` file!**

## 📁 Project Structure

```
electronics-inventory/
│
├── inventory_app.py          # Main application file
├── requirements.txt           # Python dependencies
├── .env                       # Your credentials (create this)
├── .gitignore                 # Git ignore file
├── README.md                  # This file
└── electronics_inventory.db   # Database (auto-created)
```

## 📖 Usage Guide

### Adding Items

1. Navigate to **➕ Add Item** from the sidebar
2. Fill in the form:
   - Select a category
   - Enter item name
   - Set quantity
   - Add notes/specifications
   - Enter price (optional)
3. Click **Add Item**

### Searching Items

1. Go to **🔍 Search & Manage**
2. Type in the search box to filter items
3. Search works across item names, categories, and notes
4. Click on any item to expand and see details

### Updating Quantities

1. In **🔍 Search & Manage**, expand an item
2. Enter new quantity
3. Click **Update**

### Bulk Import

1. Navigate to **📥 Bulk Import**
2. Click **Import NEW PARTS LIST** or **Import OLD PARTS LIST**
3. All items will be added to your inventory

### Viewing Dashboard

- The **📊 Dashboard** shows:
  - Total items count
  - Number of categories
  - Total quantity of all items
  - Breakdown by category
  - Complete inventory table

## 🛠️ Technologies Used

- **[Streamlit](https://streamlit.io/)** - Web application framework
- **[DuckDB](https://duckdb.org/)** - In-process SQL database
- **[Pandas](https://pandas.pydata.org/)** - Data manipulation
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - Environment variable management

## 📊 Database Schema

The inventory uses a single table with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| category | VARCHAR | Component category |
| item_name | VARCHAR | Name of the item |
| quantity | INTEGER | Number of items in stock |
| notes | VARCHAR | Specifications and notes |
| price | FLOAT | Price in ₹ (INR) |
| date_added | TIMESTAMP | When item was added |
| last_updated | TIMESTAMP | Last modification time |

## 🔧 Customization

### Adding New Categories

Edit the `CATEGORIES` list in `inventory_app.py`:

```python
CATEGORIES = [
    "Your New Category",
    # ... other categories
]
```

### Changing Currency

Replace `₹` with your currency symbol in the code.

## 🐛 Troubleshooting

### Login Issues
- Check that your `.env` file exists in the correct directory
- Verify username and password are correct
- Ensure no extra spaces in `.env` file

### Database Issues
- If database seems corrupted, delete `electronics_inventory.db`
- The app will create a fresh database on next run
- Re-import your items using bulk import

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try upgrading pip: `pip install --upgrade pip`

## 📝 Tips & Best Practices

1. **Regular Backups**: Backup `electronics_inventory.db` regularly
2. **Use Search**: Before buying new parts, search your inventory first
3. **Update Quantities**: Keep quantities current to avoid duplicate purchases
4. **Detailed Notes**: Add datasheets links or pin configurations in notes
5. **Price Tracking**: Enter prices to track your investment

## 🤝 Contributing

Feel free to fork this project and customize it for your needs!

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built for electronics hobbyists and makers
- Inspired by the need to organize growing component collections

## 📧 Support

If you encounter any issues or have suggestions, feel free to open an issue on the repository.

---

**Happy Making! 🎉**

Built with ❤️ using Streamlit and DuckDB