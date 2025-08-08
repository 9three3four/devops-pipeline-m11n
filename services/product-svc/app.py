from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# In-memory storage (use database in production)
products = [
    {"id": "1", "name": "Laptop", "price": 999.99, "category": "Electronics", "stock": 50},
    {"id": "2", "name": "Phone", "price": 699.99, "category": "Electronics", "stock": 100},
    {"id": "3", "name": "Book", "price": 19.99, "category": "Books", "stock": 200},
    {"id": "4", "name": "Headphones", "price": 149.99, "category": "Electronics", "stock": 75}
]

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'product-service',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/products', methods=['GET'])
def get_products():
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    filtered_products = products.copy()
    
    if category:
        filtered_products = [p for p in filtered_products if p['category'].lower() == category.lower()]
    
    if min_price is not None:
        filtered_products = [p for p in filtered_products if p['price'] >= min_price]
        
    if max_price is not None:
        filtered_products = [p for p in filtered_products if p['price'] <= max_price]
    
    return jsonify({
        'service': 'product-service',
        'data': filtered_products,
        'count': len(filtered_products),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'service': 'product-service',
        'data': product
    }), 200

@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    
    if not data or not all(k in data for k in ['name', 'price', 'category']):
        return jsonify({'error': 'Name, price, and category are required'}), 400
    
    new_product = {
        'id': str(uuid.uuid4()),
        'name': data['name'],
        'price': float(data['price']),
        'category': data['category'],
        'stock': data.get('stock', 0),
        'created_at': datetime.utcnow().isoformat()
    }
    
    products.append(new_product)
    
    return jsonify({
        'service': 'product-service',
        'data': new_product
    }), 201

@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    product.update({
        'name': data.get('name', product['name']),
        'price': float(data.get('price', product['price'])),
        'category': data.get('category', product['category']),
        'stock': data.get('stock', product['stock']),
        'updated_at': datetime.utcnow().isoformat()
    })
    
    return jsonify({
        'service': 'product-service',
        'data': product
    }), 200

@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    global products
    products = [p for p in products if p['id'] != product_id]
    return '', 204

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Server Error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f'Starting Product Service on port {port}')
    app.run(host='0.0.0.0', port=port, debug=debug)
