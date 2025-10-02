from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

    # File untuk menyimpan menu
MENU_FILE = 'data/menu.json'
ORDERS_FILE = 'data/orders.json'

def find_image_file(image_name):
    """Cari file gambar dengan berbagai ekstensi"""
    image_dir = 'static/images/menu'
    possible_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    
    for ext in possible_extensions:
        image_path = os.path.join(image_dir, image_name + ext)
        if os.path.exists(image_path):
            return image_name + ext

    # Jika tidak ditemukan, return None
    return None

def load_menu_with_images():
    """Load menu dan cek ketersediaan gambar"""
    menu_data = load_menu()
    # Update path gambar untuk setiap item
    for category in menu_data.values():
        for item in category:
            if 'gambar' in item:
                # Cari file gambar yang actually ada
                image_name = os.path.splitext(item['gambar'])[0]  # hapus extension
                actual_image = find_image_file(image_name)
                item['gambar_path'] = actual_image  # simpan path yang benar
    
    return menu_data

def load_menu():
        """Load data menu dari file JSON"""
        try:
            with open(MENU_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default menu jika file tidak ada
            default_menu = {
                "makanan": [
                    {"id": 1, "nama": "Nasi Goreng Spesial", "harga": 25000, "gambar": "nasi_goreng.jpg", "deskripsi": "Nasi goreng dengan telur, ayam, dan sayuran segar"},
                    {"id": 2, "nama": "Mie Ayam Bakso", "harga": 20000, "gambar": "mie_ayam.jpg", "deskripsi": "Mie ayam dengan bakso sapi pilihan"},
                    {"id": 3, "nama": "Gado-gado", "harga": 18000, "gambar": "gado_gado.jpg", "deskripsi": "Salad khas Indonesia dengan bumbu kacang"},
                    {"id": 4, "nama": "Sate Ayam", "harga": 30000, "gambar": "sate_ayam.jpg", "deskripsi": "Sate ayam dengan bumbu kacang spesial"}
                ],
                "minuman": [
                    {"id": 5, "nama": "Es Teh Manis", "harga": 5000, "gambar": "es_teh.jpg", "deskripsi": "Es teh manis segar"},
                    {"id": 6, "nama": "Jus Jeruk", "harga": 12000, "gambar": "jus_jeruk.jpg", "deskripsi": "Jus jeruk segar tanpa pengawet"},
                    {"id": 7, "nama": "Kopi Hitam", "harga": 8000, "gambar": "kopi_hitam.jpg", "deskripsi": "Kopi hitam aromatik"}
                ],
                "snack": [
                    {"id": 8, "nama": "Kentang Goreng", "harga": 15000, "gambar": "kentang_goreng.jpg", "deskripsi": "Kentang goreng renyah dengan saus"},
                    {"id": 9, "nama": "Onion Ring", "harga": 12000, "gambar": "onion_ring.jpg", "deskripsi": "Onion ring crispy"}
                ]
            }
            # Buat folder data jika belum ada
            os.makedirs('data', exist_ok=True)
            with open(MENU_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_menu, f, indent=4, ensure_ascii=False)
            return default_menu

def save_order(order_data):
        """Simpan data pesanan ke file JSON"""
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                orders = json.load(f)
        except FileNotFoundError:
            orders = []
        
        orders.append(order_data)
        
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, indent=4, ensure_ascii=False)

@app.route('/')
def home():
        """Halaman utama"""
        return render_template('index.html')

@app.route('/menu')
def menu():
    """Halaman menu makanan"""
    menu_data = load_menu()
    
    # DEBUG: Print image paths
    print("=== DEBUG IMAGE PATHS ===")
    for category_name, category_items in menu_data.items():
        for item in category_items:
            image_path = f"static/images/menu/{item['gambar']}"
            exists = os.path.exists(image_path)
            print(f"{item['nama']}: {image_path} → {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
    
    return render_template('menu.html', menu=menu_data)

@app.route('/order/<int:item_id>')
def order(item_id):
    """Halaman form pemesanan"""
    menu_data = load_menu_with_images()
    item = None
    
    for category in menu_data.values():
        for menu_item in category:
            if menu_item['id'] == item_id:
                item = menu_item
                break
        if item:
            break
    
    if not item:
        flash('Menu tidak ditemukan!', 'error')
        return redirect(url_for('menu'))
    
    return render_template('order.html', item=item)

@app.route('/process_order', methods=['POST'])
def process_order():
        """Proses data pemesanan"""
        try:
            item_id = int(request.form['item_id'])
            quantity = int(request.form['quantity'])
            customer_name = request.form['customer_name']
            customer_phone = request.form['customer_phone']
            address = request.form['address']
            notes = request.form.get('notes', '')
            
            # Load menu untuk mendapatkan detail item
            menu_data = load_menu()
            item = None
            
            for category in menu_data.values():
                for menu_item in category:
                    if menu_item['id'] == item_id:
                        item = menu_item
                        break
                if item:
                    break
            
            if not item:
                flash('Menu tidak ditemukan!', 'error')
                return redirect(url_for('menu'))
            
            # Hitung total harga
            total_price = item['harga'] * quantity
            
            # Buat data pesanan
            order_data = {
                'order_id': datetime.now().strftime("%Y%m%d%H%M%S"),
                'timestamp': datetime.now().isoformat(),
                'customer': {
                    'name': customer_name,
                    'phone': customer_phone,
                    'address': address
                },
                'order': {
                    'item_id': item_id,
                    'item_name': item['nama'],
                    'quantity': quantity,
                    'unit_price': item['harga'],
                    'total_price': total_price,
                    'notes': notes
                },
                'status': 'pending'
            }
            
            # Simpan pesanan
            save_order(order_data)
            
            return render_template('success.html', 
                                order=order_data, 
                                customer_name=customer_name)
        
        except Exception as e:
            flash(f'Terjadi error: {str(e)}', 'error')
            return redirect(url_for('menu'))

if __name__ == '__main__':
        # Pastikan folder ada
        os.makedirs('data', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static/css', exist_ok=True)
        os.makedirs('static/images', exist_ok=True)
        
        print("🚀 Starting Restaurant Website...")
        print("📧 Access at: http://localhost:5000")
        app.run(debug=True, port=5000)