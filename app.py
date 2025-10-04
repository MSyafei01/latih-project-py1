from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
from datetime import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = 'resto_baqi_secret_key'

# File untuk menyimpan data
MENU_FILE = 'data/menu.json'
ORDERS_FILE = 'data/orders.json'
PAYMENTS_FILE = 'data/payments.json'

# ===== FUNGSI UTILITAS =====
def find_image_file(image_name):
    """Cari file gambar dengan berbagai ekstensi"""
    image_dir = 'static/images/menu'
    possible_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    
    for ext in possible_extensions:
        image_path = os.path.join(image_dir, image_name + ext)
        if os.path.exists(image_path):
            return image_name + ext
    return None

def load_menu_with_images():
    """Load menu dan cek ketersediaan gambar"""
    menu_data = load_menu()
    for category in menu_data.values():
        for item in category:
            if 'gambar' in item:
                image_name = os.path.splitext(item['gambar'])[0]
                actual_image = find_image_file(image_name)
                item['gambar_path'] = actual_image
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

def save_payment(payment_data):
    """Simpan data pembayaran"""
    try:
        with open(PAYMENTS_FILE, 'r', encoding='utf-8') as f:
            payments = json.load(f)
    except FileNotFoundError:
        payments = []
    
    payments.append(payment_data)
    with open(PAYMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(payments, f, indent=4, ensure_ascii=False)

# ===== FUNGSI QRIS MANUAL =====
def generate_qris_code(amount, order_id, merchant_name="RESTO BAQI"):
    """Generate QRIS code manually"""
    try:
        # Format amount to 12 digits (QRIS standard)
        amount_str = f"{amount:012d}"
        
        # Simple QRIS-like data structure
        qris_data = f"RestoBaqi|{amount}|{order_id}|{merchant_name}"
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(qris_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for web display
        buffer = io.BytesIO()
        qr_image.save(buffer, format="JPG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/jpg;base64,{qr_base64}"
        
    except Exception as e:
        print(f"QR Generation Error: {e}")
        return generate_fallback_qr(amount, order_id)

def generate_fallback_qr(amount, order_id):
    """Fallback QR generator if main one fails"""
    try:
        simple_data = f"Payment: Rp {amount:,} | Order: {order_id}"
        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(simple_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="JPG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/jpg;base64,{qr_base64}"
    except:
        return "/static/images/qrisImage.jpg"

# ===== ROUTES UTAMA =====
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
            'status': 'pending_payment'
        }
        
        # Simpan pesanan
        save_order(order_data)
        
        # Redirect ke halaman pembayaran
        return redirect(url_for('payment_page', order_id=order_data['order_id']))
    
    except Exception as e:
        flash(f'Terjadi error: {str(e)}', 'error')
        return redirect(url_for('menu'))

@app.route('/payment/<order_id>')
def payment_page(order_id):
    """Halaman pembayaran dengan QRIS"""
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders = json.load(f)
    except FileNotFoundError:
        flash('Pesanan tidak ditemukan!', 'error')
        return redirect(url_for('menu'))
    
    order = next((o for o in orders if o['order_id'] == order_id), None)
    
    if not order:
        flash('Pesanan tidak ditemukan!', 'error')
        return redirect(url_for('menu'))
    
    return render_template('payment.html', order=order)

# ===== API PAYMENT =====
@app.route('/api/create_payment', methods=['POST'])
def create_payment():
    """Create payment dengan Manual QR Generator"""
    try:
        data = request.json
        order_id = data['order_id']
        total_amount = data['total_amount']
        customer_name = data['customer_name']
        
        print(f"Creating QR for order {order_id}, amount: {total_amount}")
        
        # Generate QR code
        qr_code_url = generate_qris_code(total_amount, order_id)
        
        # Simpan payment data
        payment_data = {
            'order_id': order_id,
            'payment_id': f"qr-{order_id}",
            'qr_code_url': qr_code_url,
            'payment_status': 'pending',
            'created_at': datetime.now().isoformat(),
            'payment_method': 'QRIS',
            'amount': total_amount,
            'customer_name': customer_name
        }
        
        save_payment(payment_data)
        
        return jsonify({
            'status': 'success',
            'payment_data': {
                'id': payment_data['payment_id'],
                'qr_code': qr_code_url,
                'order_id': order_id,
                'amount': total_amount
            },
            'qr_code_url': qr_code_url,
            'payment_id': payment_data['payment_id']
        })
        
    except Exception as e:
        print(f"Payment Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Payment failed: {str(e)}'
        }), 500

@app.route('/api/check_payment/<payment_id>')
def check_payment(payment_id):
    """Check payment status - Simulasi manual"""
    try:
        # Cari data payment
        try:
            with open(PAYMENTS_FILE, 'r', encoding='utf-8') as f:
                payments = json.load(f)
        except FileNotFoundError:
            return jsonify({'status': 'error', 'message': 'Payment not found'}), 404
        
        payment = next((p for p in payments if p['payment_id'] == payment_id), None)
        
        if not payment:
            return jsonify({'status': 'error', 'message': 'Payment not found'}), 404
        
        # Simulasi payment process
        created_time = datetime.fromisoformat(payment['created_at'])
        current_time = datetime.now()
        time_diff = (current_time - created_time).total_seconds()
        
        # Logic simulasi:
        # - 0-10 detik: pending
        # - 10-20 detik: paid
        # - >20 detik: expired
        if time_diff < 10:
            status = 'pending'
            message = '⏳ Menunggu pembayaran...'
        elif time_diff < 20:
            status = 'paid'
            message = '✅ Pembayaran berhasil!'
        else:
            status = 'expired'
            message = '❌ QR Code expired'
        
        # Update status
        payment['payment_status'] = status
        payment['updated_at'] = current_time.isoformat()
        
        # Save updated payments
        with open(PAYMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(payments, f, indent=4, ensure_ascii=False)
        
        return jsonify({
            'status': 'success',
            'payment_status': status,
            'message': message,
            'data': {
                'order_id': payment['order_id'],
                'amount': payment['amount'],
                'created_at': payment['created_at']
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/payment_success/<order_id>')
def payment_success(order_id):
    """Halaman sukses pembayaran"""
    return render_template('payment_success.html', order_id=order_id)

@app.route('/simulate_payment/<payment_id>')
def simulate_payment(payment_id):
    """Halaman untuk simulasi pembayaran (untuk testing)"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simulasi Pembayaran - Resto Baqi</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .container {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .btn {{ background: #27ae60; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
            .btn:hover {{ background: #219a52; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 Simulasi Pembayaran</h1>
            <p>Payment ID: <strong>{payment_id}</strong></p>
            <p>Gunakan halaman ini untuk testing flow pembayaran</p>
            
            <div style="margin: 20px 0;">
                <button class="btn" onclick="simulateSuccess()">✅ Simulasi Pembayaran Berhasil</button>
                <button class="btn" onclick="simulateFailed()">❌ Simulasi Pembayaran Gagal</button>
            </div>
            
            <div id="result" style="margin-top: 20px; padding: 15px; border-radius: 5px; display: none;"></div>
        </div>

        <script>
            function simulateSuccess() {{
                fetch('/api/check_payment/{payment_id}')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('result').innerHTML = 
                            '<div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 5px;">' +
                            '<h3>✅ Pembayaran Simulasi Berhasil!</h3>' +
                            '<p>Status: ' + data.payment_status + '</p>' +
                            '<p>Pesan: ' + data.message + '</p>' +
                            '</div>';
                        document.getElementById('result').style.display = 'block';
                    }});
            }}

            function simulateFailed() {{
                document.getElementById('result').innerHTML = 
                    '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px;">' +
                    '<h3>❌ Pembayaran Simulasi Gagal/Expired</h3>' +
                    '<p>Status: expired</p>' +
                    '<p>QR Code sudah kadaluarsa</p>' +
                    '</div>';
                document.getElementById('result').style.display = 'block';
            }}
        </script>
    </body>
    </html>
    """

@app.route('/test_qr')
def test_qr():
    """Test QR code generation"""
    try:
        # Test generate QR code
        qr_url = generate_qris_code(25000, "TEST-ORDER-123")
        
        return f"""
        <h1>✅ QR Generator Working!</h1>
        <p>QR Code berhasil digenerate:</p>
        <img src="{qr_url}" alt="Test QR Code" style="border: 2px solid #ccc; padding: 10px;">
        <p>Data: RestoBaqi|25000|TEST-ORDER-123|RESTO BAQI</p>
        """
    except Exception as e:
        return f"<h1>❌ QR Generator Error: {str(e)}</h1>"

# ===== MAIN =====
if __name__ == '__main__':
    # Pastikan folder ada
    os.makedirs('data', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🚀 Starting Restaurant Website with Manual QR...")
    print("📧 Access at: http://localhost:5000")
    print("💡 Tips: Gunakan http://localhost:5000/simulate_payment/{payment_id} untuk testing")
    app.run(debug=True, port=5000)