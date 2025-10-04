class PaymentHandler {
    constructor() {
        this.orderId = document.querySelector('.payment-header strong').textContent;
        this.paymentId = null;
        this.checkInterval = null;
        this.init();
    }

    init() {
        document.getElementById('payButton').addEventListener('click', () => {
            this.createPayment();
        });

        document.getElementById('checkStatus')?.addEventListener('click', () => {
            this.checkPaymentStatus();
        });
    }

    async createPayment() {
        const payButton = document.getElementById('payButton');
        const processingDiv = document.getElementById('paymentProcessing');
        const qrisDisplay = document.getElementById('qrisDisplay');

        // Show loading
        payButton.style.display = 'none';
        processingDiv.style.display = 'block';

        try {
            const response = await fetch('/api/create_payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    order_id: this.orderId,
                    total_amount: this.getTotalAmount(),
                    customer_name: this.getCustomerName()
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.paymentId = result.payment_id;
                
                // Show QR Code
                processingDiv.style.display = 'none';
                qrisDisplay.style.display = 'block';
                document.getElementById('qrCodeImage').src = result.qr_code_url;
                
                // Start checking payment status
                this.startPaymentPolling();
            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            alert('Error: ' + error.message);
            payButton.style.display = 'block';
            processingDiv.style.display = 'none';
        }
    }

    startPaymentPolling() {
        // Check every 5 seconds
        this.checkInterval = setInterval(() => {
            this.checkPaymentStatus();
        }, 5000);
        
        // Check immediately
        this.checkPaymentStatus();
    }

    async checkPaymentStatus() {
        if (!this.paymentId) return;

        try {
            const response = await fetch(`/api/check_payment/${this.paymentId}`);
            const result = await response.json();

            if (result.status === 'success') {
                this.updatePaymentUI(result.payment_status, result.data);
            }
        } catch (error) {
            console.error('Status check error:', error);
        }
    }

    updatePaymentUI(status, data) {
        const statusElement = document.getElementById('statusMessage');
        
        switch(status) {
            case 'settlement':
                statusElement.innerHTML = '✅ Pembayaran Berhasil!';
                statusElement.className = 'status-success';
                clearInterval(this.checkInterval);
                setTimeout(() => {
                    window.location.href = `/payment_success/${this.orderId}`;
                }, 2000);
                break;
                
            case 'pending':
                statusElement.innerHTML = '⏳ Menunggu pembayaran...';
                statusElement.className = 'status-pending';
                break;
                
            case 'expire':
                statusElement.innerHTML = '❌ Pembayaran kadaluarsa';
                statusElement.className = 'status-failed';
                clearInterval(this.checkInterval);
                break;
                
            case 'cancel':
            case 'deny':
                statusElement.innerHTML = '❌ Pembayaran gagal';
                statusElement.className = 'status-failed';
                clearInterval(this.checkInterval);
                break;
        }
    }

    getTotalAmount() {
        // Extract total from order data
        const totalText = document.querySelector('.btn-pay').textContent;
        const match = totalText.match(/Rp (\d+(?:\.\d+)*)/);
        return match ? parseInt(match[1].replace(/\./g, '')) : 0;
    }

    getCustomerName() {
        return document.querySelector('.order-details p:last-child strong').nextSibling.textContent.trim();
    }
}

// Initialize payment handler
document.addEventListener('DOMContentLoaded', () => {
    new PaymentHandler();
});