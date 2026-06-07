"""
BazaarAPI — Deliberately Vulnerable Indian Shopping API
Looks & feels like a real Indian e-commerce platform.

INTENTIONAL VULNERABILITIES (OWASP API Top 10 — 2023):
  API1  — BOLA/IDOR   : /api/users/<id>, /api/orders/<id>
  API2  — Broken Auth : JWT alg:none, weak secret, NoSQL bypass
  API3  — Mass Assign : /api/register accepts role/isAdmin/balance
  API4  — No Rate Limit: /api/login, /api/register unlimited
  API5  — BFLA        : /api/admin/users — no admin check
  API7  — SSRF        : /api/fetch?url=
  API8  — CORS *      : wildcard + missing security headers
  API9  — Info Leak   : /swagger.json, /.env, /api/health
  API10 — GraphQL     : introspection enabled

FOR SECURITY TESTING / FYP DEMO ONLY
"""

import json, time, base64, os, urllib.request
from flask import Flask, request, jsonify, Response, g, send_from_directory
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

# ─── Indian User Database ────────────────────────────────────────────────────

USERS = {
    1: {
        "id": 1, "name": "Arjun Sharma", "username": "arjun_admin",
        "password": "admin@123", "email": "arjun@bazaarapi.in",
        "phone": "+91-9876543210", "role": "admin",
        "balance": 999999, "gst_number": "27AABCU9603R1ZX",
        "credit_card": "4111-1111-1111-1111", "cvv": "123",
        "address": "204, Andheri West, Mumbai, Maharashtra - 400058",
    },
    2: {
        "id": 2, "name": "Priya Patel", "username": "priya_patel",
        "password": "priya123", "email": "priya@gmail.com",
        "phone": "+91-9123456789", "role": "user",
        "balance": 5000, "upi_id": "priya@paytm",
        "address": "12B, Koramangala, Bengaluru, Karnataka - 560034",
    },
    3: {
        "id": 3, "name": "Ravi Kumar", "username": "ravi_kumar",
        "password": "password", "email": "ravi@yahoo.com",
        "phone": "+91-8899001122", "role": "user",
        "balance": 1500, "upi_id": "ravi@upi",
        "address": "56, Lajpat Nagar, New Delhi - 110024",
    },
    4: {
        "id": 4, "name": "Meera Iyer", "username": "meera_iyer",
        "password": "meera@456", "email": "meera@hotmail.com",
        "phone": "+91-7700112233", "role": "seller",
        "balance": 85000, "gst_number": "33AADCF5823R1ZY",
        "address": "7, T. Nagar, Chennai, Tamil Nadu - 600017",
    },
}

ORDERS = {
    1:  {"id": 1,  "user_id": 2, "product": "Banarasi Silk Saree", "qty": 1,
         "amount": 2499.00, "status": "delivered", "payment": "UPI",
         "address": "12B, Koramangala, Bengaluru"},
    2:  {"id": 2,  "user_id": 2, "product": "OnePlus Nord CE 3", "qty": 1,
         "amount": 24999.00, "status": "shipped", "payment": "EMI",
         "address": "12B, Koramangala, Bengaluru"},
    3:  {"id": 3,  "user_id": 3, "product": "Kurta Pyjama Set", "qty": 2,
         "amount": 1198.00, "status": "pending", "payment": "COD",
         "address": "56, Lajpat Nagar, New Delhi"},
    4:  {"id": 4,  "user_id": 4, "product": "Pressure Cooker 5L", "qty": 1,
         "amount": 1899.00, "status": "processing", "payment": "Card",
         "address": "7, T. Nagar, Chennai"},
}

PRODUCTS = [
    {"id": 1,  "name": "Banarasi Silk Saree",              "brand": "Kanjivaram",
     "price": 2499,  "mrp": 4999,  "category": "Women Fashion",
     "seller": "SareeWala Store",      "stock": 45,   "rating": 4.5,
     "gst": "12%", "sku": "SAR-001-RED",
     "image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400&q=80",
     "description": "Pure Banarasi silk saree with zari work. Perfect for weddings and festivals."},

    {"id": 2,  "name": "Men's Kurta Pyjama Set",           "brand": "Manyavar",
     "price": 599,   "mrp": 1199,  "category": "Men Fashion",
     "seller": "Ethnic Wear Hub",      "stock": 120,  "rating": 4.2,
     "gst": "12%", "sku": "KPS-002-WHT",
     "image": "https://images.unsplash.com/photo-1583391733956-6c78276477e1?w=400&q=80",
     "description": "Cotton kurta pyjama set. Ideal for Eid, Diwali and casual occasions."},

    {"id": 3,  "name": "OnePlus Nord CE 3 (8GB/128GB)",    "brand": "OnePlus",
     "price": 24999, "mrp": 27999, "category": "Smartphones",
     "seller": "Reliance Digital",     "stock": 30,   "rating": 4.7,
     "gst": "18%", "sku": "OP-NORD-CE3",
     "image": "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=400&q=80",
     "description": "50MP camera | 5000mAh battery | 80W SUPERVOOC charging."},

    {"id": 4,  "name": "Prestige Pressure Cooker 5L",      "brand": "Prestige",
     "price": 1899,  "mrp": 2800,  "category": "Kitchen",
     "seller": "Kitchen King",         "stock": 80,   "rating": 4.6,
     "gst": "12%", "sku": "PRE-PC-5L",
     "image": "https://images.unsplash.com/photo-1585515320310-259814833e62?w=400&q=80",
     "description": "Hard anodised aluminium pressure cooker. Safety valve. ISI certified."},

    {"id": 5,  "name": "Patanjali Aloevera Gel 150g",      "brand": "Patanjali",
     "price": 99,    "mrp": 130,   "category": "Health & Beauty",
     "seller": "Patanjali Official",   "stock": 500,  "rating": 4.0,
     "gst": "18%", "sku": "PAT-ALO-150",
     "image": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400&q=80",
     "description": "Pure aloe vera gel. Moisturises skin, reduces acne and sunburn."},

    {"id": 6,  "name": "Levi's 511 Slim Fit Jeans",        "brand": "Levi's",
     "price": 1799,  "mrp": 3999,  "category": "Men Fashion",
     "seller": "Levi's India",         "stock": 200,  "rating": 4.4,
     "gst": "12%", "sku": "LEV-511-BLU",
     "image": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&q=80",
     "description": "Classic slim fit jeans in dark blue wash. 99% cotton 1% elastane."},

    {"id": 7,  "name": "Tata Sampann Chana Dal 1kg",       "brand": "Tata",
     "price": 89,    "mrp": 110,   "category": "Grocery",
     "seller": "Tata Consumer",        "stock": 1000, "rating": 4.3,
     "gst": "0%",  "sku": "TAT-DAL-1KG",
     "image": "https://images.unsplash.com/photo-1585669756870-45939dc1c8c6?w=400&q=80",
     "description": "Premium chana dal. Rich in protein. No preservatives. Farm fresh."},

    {"id": 8,  "name": "Amul Butter 500g",                 "brand": "Amul",
     "price": 245,   "mrp": 260,   "category": "Grocery",
     "seller": "Amul Official",        "stock": 300,  "rating": 4.8,
     "gst": "0%",  "sku": "AML-BTR-500",
     "image": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&q=80",
     "description": "India's favourite butter. Made from fresh cream. Pasteurised."},

    {"id": 9,  "name": "boAt Rockerz 450 Bluetooth Headphone","brand": "boAt",
     "price": 1299,  "mrp": 2990,  "category": "Electronics",
     "seller": "boAt Official Store",  "stock": 150,  "rating": 4.3,
     "gst": "18%", "sku": "BOA-ROC-450",
     "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80",
     "description": "15hr battery | 40mm drivers | foldable design | mic for calls."},

    {"id": 10, "name": "Nike Air Max 270 Running Shoes",   "brand": "Nike",
     "price": 7495,  "mrp": 12995, "category": "Footwear",
     "seller": "Nike India Official",  "stock": 60,   "rating": 4.5,
     "gst": "18%", "sku": "NIK-AM270-BLK",
     "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80",
     "description": "Max Air cushioning | breathable mesh upper | rubber outsole."},

    {"id": 11, "name": "Lakme Absolute Skin Natural Mousse","brand": "Lakme",
     "price": 349,   "mrp": 499,   "category": "Health & Beauty",
     "seller": "Lakme Official",       "stock": 400,  "rating": 4.1,
     "gst": "18%", "sku": "LAK-SKN-NM",
     "image": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=400&q=80",
     "description": "Lightweight foundation. Natural finish. SPF 8. 8hr coverage."},

    {"id": 12, "name": "Samsung 55\" 4K QLED Smart TV",   "brand": "Samsung",
     "price": 54999, "mrp": 74999, "category": "Electronics",
     "seller": "Samsung SmartPlaza",   "stock": 15,   "rating": 4.6,
     "gst": "28%", "sku": "SAM-TV-55Q",
     "image": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400&q=80",
     "description": "4K QLED | Tizen OS | Netflix & Prime built-in | 3yr warranty."},

    {"id": 13, "name": "Himalaya Neem Face Wash 150ml",   "brand": "Himalaya",
     "price": 99,    "mrp": 125,   "category": "Health & Beauty",
     "seller": "Himalaya Wellness",    "stock": 800,  "rating": 4.4,
     "gst": "18%", "sku": "HIM-NEEM-FW",
     "image": "https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=400&q=80",
     "description": "Neem & turmeric formula. Removes oil & bacteria. Dermat. tested."},

    {"id": 14, "name": "Wildcraft 45L Hiking Backpack",   "brand": "Wildcraft",
     "price": 1799,  "mrp": 3499,  "category": "Sports",
     "seller": "Wildcraft Store",      "stock": 90,   "rating": 4.2,
     "gst": "12%", "sku": "WLD-BP-45L",
     "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&q=80",
     "description": "Waterproof | ergonomic straps | laptop sleeve | rain cover."},

    {"id": 15, "name": "Haldiram's Aloo Bhujia 400g",     "brand": "Haldiram's",
     "price": 120,   "mrp": 150,   "category": "Grocery",
     "seller": "Haldiram's Official",  "stock": 600,  "rating": 4.7,
     "gst": "5%",  "sku": "HAL-ALB-400",
     "image": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&q=80",
     "description": "Crispy aloo bhujia. Pure sunflower oil. No artificial colours."},

    {"id": 16, "name": "Redmi Note 13 Pro (12GB/256GB)",  "brand": "Xiaomi",
     "price": 26999, "mrp": 29999, "category": "Smartphones",
     "seller": "Mi India",             "stock": 50,   "rating": 4.5,
     "gst": "18%", "sku": "RED-N13P-256",
     "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400&q=80",
     "description": "200MP camera | AMOLED display | 5100mAh | 67W turbo charging."},

    {"id": 17, "name": "Titan Edge Slim Wristwatch",       "brand": "Titan",
     "price": 4995,  "mrp": 6995,  "category": "Accessories",
     "seller": "Titan World",          "stock": 35,   "rating": 4.6,
     "gst": "18%", "sku": "TIT-EDGE-SLV",
     "image": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&q=80",
     "description": "World's slimmest watch. Sapphire crystal glass. WR 30m."},

    {"id": 18, "name": "Parle-G Original Biscuits 800g",  "brand": "Parle",
     "price": 65,    "mrp": 75,    "category": "Grocery",
     "seller": "Parle Products",       "stock": 2000, "rating": 4.9,
     "gst": "0%",  "sku": "PAR-G-800",
     "image": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400&q=80",
     "description": "India's favourite biscuit since 1938. Glucose enriched."},

    {"id": 19, "name": "Bajaj Mixie 500W Mixer Grinder",  "brand": "Bajaj",
     "price": 1899,  "mrp": 3200,  "category": "Kitchen",
     "seller": "Bajaj Electricals",    "stock": 70,   "rating": 4.3,
     "gst": "18%", "sku": "BAJ-MG-500W",
     "image": "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=400&q=80",
     "description": "500W motor | 3 SS jars | 2yr warranty | ISI mark."},

    {"id": 20, "name": "Forest Essentials Sandalwood Soap","brand": "Forest Essentials",
     "price": 395,   "mrp": 450,   "category": "Health & Beauty",
     "seller": "Forest Essentials",    "stock": 200,  "rating": 4.7,
     "gst": "18%", "sku": "FE-SAN-SOAP",
     "image": "https://images.unsplash.com/photo-1607006333439-505849b59f69?w=400&q=80",
     "description": "Handmade Ayurvedic soap with pure sandalwood oil. Cruelty-free."},

    {"id": 21, "name": "JBL Flip 6 Waterproof Speaker",   "brand": "JBL",
     "price": 8999,  "mrp": 11999, "category": "Electronics",
     "seller": "JBL India Official",   "stock": 40,   "rating": 4.6,
     "gst": "18%", "sku": "JBL-FLIP6-BLU",
     "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&q=80",
     "description": "IP67 waterproof | 12hr battery | Bold JBL Original Pro Sound."},

    {"id": 22, "name": "Allen Solly Formal Shirt (XL)",   "brand": "Allen Solly",
     "price": 1199,  "mrp": 2499,  "category": "Men Fashion",
     "seller": "Aditya Birla Fashion", "stock": 150,  "rating": 4.3,
     "gst": "12%", "sku": "AS-SHIRT-XL-WHT",
     "image": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=400&q=80",
     "description": "100% cotton formal shirt. Machine washable. Wrinkle resistant."},

    {"id": 23, "name": "Good Earth Assam Gold Tea 250g",  "brand": "Good Earth",
     "price": 349,   "mrp": 449,   "category": "Grocery",
     "seller": "Tea Board India",      "stock": 300,  "rating": 4.5,
     "gst": "5%",  "sku": "GE-TEA-250",
     "image": "https://images.unsplash.com/photo-1564890369478-c89ca6d9cde9?w=400&q=80",
     "description": "Single estate Assam tea. Strong malty flavour. 100 cups per pack."},

    {"id": 24, "name": "Crompton 1.5T 5-Star Inverter AC","brand": "Crompton",
     "price": 35990, "mrp": 46990, "category": "Electronics",
     "seller": "Crompton Greaves",     "stock": 20,   "rating": 4.4,
     "gst": "28%", "sku": "CRO-AC-15T5S",
     "image": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&q=80",
     "description": "5-star BEE rated | PM 2.5 filter | Wi-Fi | 5yr compressor warranty."},

    {"id": 25, "name": "Maaza Mango Drink 600ml (Pack 24)","brand": "Coca-Cola India",
     "price": 480,   "mrp": 576,   "category": "Grocery",
     "seller": "CCI Distribution",     "stock": 400,  "rating": 4.6,
     "gst": "12%", "sku": "MAZ-MNG-600X24",
     "image": "https://images.unsplash.com/photo-1546173159-315724a31696?w=400&q=80",
     "description": "Real mango pulp. No artificial colours. India's No.1 mango drink."},

    {"id": 26, "name": "Wildfire Yoga Mat 6mm Non-Slip",  "brand": "Wildfire",
     "price": 599,   "mrp": 999,   "category": "Sports",
     "seller": "Fitness India",        "stock": 250,  "rating": 4.1,
     "gst": "18%", "sku": "WF-YM-6MM",
     "image": "https://images.unsplash.com/photo-1601925228010-9c49ce7e4a39?w=400&q=80",
     "description": "6mm thick | non-slip texture | carrying strap | eco TPE material."},

    {"id": 27, "name": "Fabindia Handblock Print Dupatta", "brand": "Fabindia",
     "price": 799,   "mrp": 1499,  "category": "Women Fashion",
     "seller": "Fabindia Official",    "stock": 80,   "rating": 4.5,
     "gst": "5%",  "sku": "FAB-DUP-BLK",
     "image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400&q=80",
     "description": "Hand block printed cotton dupatta. Artisan crafted from Rajasthan."},

    {"id": 28, "name": "Classmate 6-Subject Spiral Notebook","brand": "Classmate",
     "price": 199,   "mrp": 280,   "category": "Stationery",
     "seller": "ITC Classmate",        "stock": 500,  "rating": 4.2,
     "gst": "12%", "sku": "CLS-NB-6S",
     "image": "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=400&q=80",
     "description": "300 pages | ruled | spiral binding | eco-friendly paper."},
]

COUPONS = {
    "DIWALI50": 50, "SALE100": 100,
    "NEWUSER200": 200, "BHARAT10": 10
}

REGISTERED_USERS = dict(USERS)

# ─── JWT Helpers (intentionally weak — secret = 'bazaar') ───────────────────

def b64url(data):
    return base64.urlsafe_b64encode(
        json.dumps(data).encode()).rstrip(b"=").decode()

def make_jwt(user_id, role="user"):
    header  = b64url({"alg": "HS256", "typ": "JWT"})
    payload = b64url({"sub": str(user_id), "role": role, "exp": 9999999999})
    import hmac, hashlib
    sig = hmac.new(b"bazaar", f"{header}.{payload}".encode(),
                   hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{header}.{payload}.{signature}"

def verify_jwt(token):
    """API2: Accepts alg:none — no signature validation."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        pad = lambda s: s + "=" * (4 - len(s) % 4)
        header  = json.loads(base64.urlsafe_b64decode(pad(parts[0])))
        payload = json.loads(base64.urlsafe_b64decode(pad(parts[1])))
        if header.get("alg", "").lower() == "none":
            return payload          # VULN: accepts unsigned token!
        return payload              # VULN: skips signature verify
    except Exception:
        return None

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized", "message": "Please login first"}), 401
        payload = verify_jwt(auth[7:])
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        g.user_id = int(payload.get("sub", 0))
        g.role    = payload.get("role", "user")
        return f(*args, **kwargs)
    return decorated

# ─── API8: No security headers ───────────────────────────────────────────────

@app.after_request
def add_headers(response):
    origin = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Origin"]      = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"]     = "*"
    response.headers["Access-Control-Allow-Headers"]     = "Authorization, Content-Type"
    response.headers["X-Powered-By"] = "BazaarAPI/2.1 Flask"
    response.headers["Server"]        = "BazaarAPI-Prod/2.1"
    # Missing: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
    return response

# ─── Root & Landing ───────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "TRACE"])
def index():
    if request.method == "TRACE":
        return Response(request.data, mimetype="message/http")
    # Serve the real Indian shopping website
    return send_from_directory(os.path.dirname(__file__), "index.html")

@app.route("/api/info")
def api_info():
    """JSON info endpoint for API clients."""
    return jsonify({
        "platform": "BazaarAPI",
        "tagline":  "India Ka Apna Online Bazaar",
        "version":  "2.1.0",
        "status":   "live",
        "docs":     "/docs",
        "swagger":  "/swagger.json",
        "endpoints": {
            "auth":     ["/api/v1/login", "/api/v1/register", "/api/v1/me"],
            "products": ["/api/v1/products", "/api/v1/products/<id>"],
            "orders":   ["/api/v1/orders",   "/api/v1/orders/<id>"],
            "users":    ["/api/v1/users",     "/api/v1/users/<id>"],
            "admin":    ["/api/v1/admin/users", "/api/v1/admin/config"],
            "misc":     ["/api/v1/fetch", "/api/v1/ping", "/api/v1/coupon"],
        },
        "support": "support@bazaarapi.in",
        "company": "BazaarAPI Technologies Pvt. Ltd., Mumbai, India",
    })

@app.route("/<path:path>", methods=["OPTIONS"])
def options(path):
    return jsonify({}), 200

# ─── API9: Swagger + env exposed ─────────────────────────────────────────────

@app.route("/swagger.json")
@app.route("/openapi.json")
@app.route("/api-docs")
def swagger():
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title":   "BazaarAPI — Indian Shopping Platform",
            "version": "2.1.0",
            "description": "REST API for BazaarAPI e-commerce platform",
            "contact":  {"email": "dev@bazaarapi.in"},
        },
        "servers": [{"url": "/", "description": "Production"}],
        "paths": {
            "/api/v1/login":         {"post": {"summary": "User login"}},
            "/api/v1/register":      {"post": {"summary": "Register new user"}},
            "/api/v1/products":      {"get":  {"summary": "List all products"}},
            "/api/v1/users/{id}":    {"get":  {"summary": "Get user profile"}},
            "/api/v1/orders/{id}":   {"get":  {"summary": "Get order details"}},
            "/api/v1/admin/users":   {"get":  {"summary": "Admin: all users"}},
            "/api/v1/fetch":         {"get":  {"summary": "Fetch external URL"}},
        },
    })

@app.route("/.env")
def env_file():
    return Response(
        "# BazaarAPI Production Config\n"
        "SECRET_KEY=bazaar_super_secret_prod_2024\n"
        "JWT_SECRET=bazaar\n"
        "DB_HOST=db.bazaarapi.in\n"
        "DB_PASSWORD=BazaarDB@Prod#2024\n"
        "RAZORPAY_KEY_ID=rzp_live_FAKEFAKEFAKE\n"
        "RAZORPAY_KEY_SECRET=FAKESECRETKEY123456\n"
        "AWS_ACCESS_KEY=AKIAFAKE0000000000IN\n"
        "AWS_SECRET=fakeawssecretkey000000000000bazaar\n"
        "PAYTM_MERCHANT_KEY=FakePAYTMKey@2024\n"
        "SMTP_PASSWORD=BazaarMail@2024\n"
        "REDIS_URL=redis://redis.bazaarapi.in:6379\n",
        mimetype="text/plain"
    )

@app.route("/api/v1/health")
@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "BazaarAPI",
        "db": "mysql://db.bazaarapi.in:3306/bazaardb",
        "redis": "redis://redis.bazaarapi.in:6379",
        "internal_ip": "10.0.1.45",
        "debug": True,
        "env": "production",
        "version": "2.1.0",
    })

# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.route("/api/v1/login", methods=["POST"])
def login():
    """API2 + API4: Broken auth, no rate limit."""
    data     = request.get_json(force=True) or {}
    username = data.get("username", "") or data.get("email", "")
    password = data.get("password", "")

    # API2: NoSQL injection bypass
    if isinstance(password, dict) or isinstance(username, dict):
        user = list(USERS.values())[0]
        return jsonify({
            "success": True,
            "token":   make_jwt(user["id"], user["role"]),
            "user":    {"id": user["id"], "name": user["name"], "role": user["role"]},
            "message": "Login successful",
        })

    for uid, user in USERS.items():
        if (user["username"] == username or user["email"] == username) \
                and user["password"] == password:
            return jsonify({
                "success": True,
                "token":   make_jwt(user["id"], user["role"]),
                "user": {
                    "id":    user["id"],
                    "name":  user["name"],
                    "email": user["email"],
                    "role":  user["role"],
                },
            })
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route("/api/v1/register", methods=["POST"])
def register():
    """API3: Mass assignment — accepts role, isAdmin, balance."""
    data   = request.get_json(force=True) or {}
    new_id = max(REGISTERED_USERS.keys()) + 1
    user = {
        "id":          new_id,
        "name":        data.get("name", f"User{new_id}"),
        "username":    data.get("username", f"user{new_id}"),
        "email":       data.get("email", ""),
        "phone":       data.get("phone", ""),
        "password":    data.get("password", ""),
        "balance":     data.get("balance", 0),           # VULN
        "credits":     data.get("credits", 0),           # VULN
        "cashback":    data.get("cashback", 0),          # VULN
        "role":        data.get("role", "user"),          # VULN: set role=admin
        "isAdmin":     data.get("isAdmin", False),        # VULN
        "is_admin":    data.get("is_admin", False),       # VULN
        "verified":    data.get("verified", False),       # VULN
        "seller":      data.get("seller", False),         # VULN
        "permissions": data.get("permissions", []),       # VULN
    }
    REGISTERED_USERS[new_id] = user
    return jsonify({
        "success": True,
        "message": "Account created successfully! Welcome to BazaarAPI",
        "user":    user,
        "token":   make_jwt(new_id, user["role"]),
    }), 201

@app.route("/api/v1/me")
@auth_required
def me():
    user = USERS.get(g.user_id) or REGISTERED_USERS.get(g.user_id)
    if not user:
        return jsonify({"id": g.user_id, "role": g.role})
    return jsonify({k: v for k, v in user.items() if k != "password"})

# ─── USERS ────────────────────────────────────────────────────────────────────

@app.route("/api/v1/users")
@auth_required
def list_users():
    """API5: BFLA — any authenticated user can list all users."""
    return jsonify({
        "success": True,
        "users": [
            {k: v for k, v in u.items() if k != "password"}
            for u in USERS.values()
        ],
        "total": len(USERS),
    })

@app.route("/api/v1/users/<int:user_id>")
@auth_required
def get_user(user_id):
    """API1: BOLA/IDOR — no ownership check."""
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"success": True, "user": user})   # Returns credit card, CVV!

@app.route("/api/v1/users/<int:user_id>", methods=["PUT"])
@auth_required
def update_user(user_id):
    """API1 + API3: IDOR + mass assignment on update."""
    data = request.get_json(force=True) or {}
    if user_id not in USERS:
        return jsonify({"error": "Not found"}), 404
    USERS[user_id].update(data)
    return jsonify({"success": True, "user": USERS[user_id]})

# ─── PRODUCTS ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/products")
def list_products():
    """API3: SQL injection simulation in search param. API4: No pagination limit."""
    search   = request.args.get("search", "")
    category = request.args.get("category", "")
    limit    = request.args.get("limit", 100)   # API4: no max

    if any(p in search.lower() for p in
           ["'", '"', " or ", " and ", "union", "--", "sleep(", "waitfor", ";"]):
        return jsonify({
            "error":   "Database error",
            "detail":  f"MySQLSyntaxErrorException: You have an error in your SQL syntax near "
                       f"'SELECT * FROM products WHERE name LIKE '%{search}%' LIMIT {limit}'",
            "sqlstate":"42000",
            "db_host": "db.bazaarapi.in",
        }), 500

    results = [
        p for p in PRODUCTS
        if (not search or search.lower() in p["name"].lower())
        and (not category or p["category"].lower() == category.lower())
    ]
    return jsonify({"success": True, "products": results, "total": len(results)})

@app.route("/api/v1/products/<int:product_id>")
def get_product(product_id):
    p = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not p:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"success": True, "product": p})

# ─── ORDERS ───────────────────────────────────────────────────────────────────

@app.route("/api/v1/orders")
@auth_required
def list_orders():
    """API1: Returns ALL orders regardless of user."""
    return jsonify({"success": True, "orders": list(ORDERS.values()), "total": len(ORDERS)})

@app.route("/api/v1/orders/<int:order_id>")
@auth_required
def get_order(order_id):
    """API1: IDOR — no ownership check."""
    order = ORDERS.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"success": True, "order": order})

@app.route("/api/v1/orders", methods=["POST"])
@auth_required
def create_order():
    """API6: Business logic flaw — accepts negative amounts."""
    data = request.get_json(force=True) or {}
    qty  = data.get("qty", 1)       # Accepts -1 → negative charge
    amt  = data.get("amount", 0)    # Accepts negative → refund abuse
    new_id = max(ORDERS.keys()) + 1
    order = {
        "id":       new_id,
        "user_id":  g.user_id,
        "product":  data.get("product", "Unknown"),
        "qty":      qty,
        "amount":   amt,
        "status":   "pending",
        "payment":  data.get("payment", "COD"),
    }
    ORDERS[new_id] = order
    return jsonify({"success": True, "order": order, "message": "Order placed successfully!"}), 201

# ─── ADMIN ────────────────────────────────────────────────────────────────────

@app.route("/api/v1/admin/users")
@auth_required
def admin_users():
    """API5: BFLA — no role=admin check."""
    return jsonify({
        "success": True,
        "users":   list(USERS.values()),   # Full data incl. passwords & cards!
        "total":   len(USERS),
        "note":    "Admin endpoint — all user PII including payment details",
    })

@app.route("/api/v1/admin/config")
@auth_required
def admin_config():
    """API5: Leaks secrets to any authenticated user."""
    return jsonify({
        "db":             "mysql://admin:BazaarDB@Prod#2024@db.bazaarapi.in/bazaardb",
        "jwt_secret":     "bazaar",
        "razorpay_key":   "rzp_live_FAKEFAKEFAKE",
        "paytm_key":      "FakePAYTMKey@2024",
        "smtp_password":  "BazaarMail@2024",
        "debug":          True,
        "admin_email":    "arjun@bazaarapi.in",
        "internal_subnet":"10.0.1.0/24",
    })

@app.route("/api/v1/admin/transactions")
@auth_required
def admin_transactions():
    return jsonify({
        "transactions": [
            {"id": "TXN001", "user": "priya@gmail.com", "amount": 24999,
             "card": "4111****1111", "upi": "priya@paytm", "status": "success"},
            {"id": "TXN002", "user": "ravi@yahoo.com",  "amount": 1198,
             "card": None, "upi": "ravi@upi", "status": "success"},
        ]
    })

# ─── API7: SSRF ───────────────────────────────────────────────────────────────

@app.route("/api/v1/fetch")
@auth_required
def fetch():
    """API7: SSRF — no URL validation."""
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "url parameter is required"}), 400
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            content = r.read(2048).decode("utf-8", errors="replace")
        return jsonify({"url": url, "status": r.status, "content": content})
    except Exception as e:
        return jsonify({"error": str(e), "url": url}), 500

# ─── Command Injection simulation ─────────────────────────────────────────────

@app.route("/api/v1/ping")
@auth_required
def ping():
    host = request.args.get("host", "bazaarapi.in")
    if any(c in host for c in [";", "|", "&", "`", "$("]):
        return jsonify({
            "command":    f"ping -c 1 {host}",
            "output":     "uid=33(www-data) gid=33(www-data) groups=33(www-data)\n"
                          "root:x:0:0:root:/root:/bin/bash\n"
                          "bazaarapi:x:1001:1001::/home/bazaarapi:/bin/bash",
            "vulnerable": True,
        })
    return jsonify({
        "command": f"ping {host}",
        "output":  f"PING {host}: 56 bytes of data. 64 bytes: icmp_seq=1 ttl=64 time=1.2ms",
    })

# ─── Coupon / API4 ────────────────────────────────────────────────────────────

@app.route("/api/v1/coupon", methods=["POST"])
@auth_required
def apply_coupon():
    """API4+API6: No rate limit, coupons reusable."""
    data = request.get_json(force=True) or {}
    code = data.get("code", "").upper()
    discount = COUPONS.get(code, 0)
    return jsonify({
        "success":  discount > 0,
        "code":     code,
        "discount": f"₹{discount}",
        "message":  f"Coupon applied! You save ₹{discount}" if discount else "Invalid coupon code",
    })

# ─── GraphQL (introspection enabled) ─────────────────────────────────────────

@app.route("/graphql", methods=["GET", "POST"])
def graphql():
    data  = request.get_json(force=True) or {}
    query = data.get("query", "")
    if "__schema" in query or "__typename" in query:
        return jsonify({"data": {"__schema": {
            "queryType": {"name": "Query"},
            "types": [
                {"name": "Query",    "fields": [{"name": "user"}, {"name": "product"}, {"name": "order"}]},
                {"name": "User",     "fields": [{"name": "id"}, {"name": "name"}, {"name": "email"},
                                                {"name": "password"}, {"name": "creditCard"}, {"name": "upi"}]},
                {"name": "Product",  "fields": [{"name": "id"}, {"name": "name"}, {"name": "price"}]},
                {"name": "Mutation", "fields": [{"name": "createUser"}, {"name": "deleteUser"},
                                                {"name": "updateBalance"}, {"name": "applyDiscount"}]},
            ]
        }}})
    if "user" in query:
        return jsonify({"data": {"user": {"id": 1, "name": "Arjun Sharma", "role": "admin"}}})
    return jsonify({"errors": [{"message": "Syntax error in query"}]})

# ─── JWKS ─────────────────────────────────────────────────────────────────────

@app.route("/jwks.json")
@app.route("/.well-known/jwks.json")
def jwks():
    return jsonify({"keys": [{
        "kty": "RSA", "alg": "RS256", "use": "sig",
        "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc",
        "e": "AQAB",
    }]})

# ─── XML / XXE ────────────────────────────────────────────────────────────────

@app.route("/api/v1/import", methods=["POST"])
@auth_required
def import_data():
    body = request.get_data(as_text=True)
    ct   = request.content_type or ""
    if "xml" in ct.lower() or body.strip().startswith("<?xml"):
        if "SYSTEM" in body and ("file://" in body or "http://" in body):
            return jsonify({
                "status":     "processed",
                "data":       "root:x:0:0:root:/root:/bin/bash\nbazaarapi:x:1001:1001::/home/bazaarapi",
                "vulnerable": True,
                "note":       "XXE successful",
            })
        return jsonify({"status": "ok", "records_imported": 12})
    return jsonify({"error": "Content-Type must be application/xml"}), 415

# ─── Version / Docs ───────────────────────────────────────────────────────────

@app.route("/api/v1/version")
def version():
    return jsonify({
        "platform":     "BazaarAPI",
        "version":      "2.1.0",
        "api_version":  "v1",
        "deprecated":   ["/api/v0/", "/api/beta/"],   # API9: exposes old versions
        "python":       "3.11.4",
        "flask":        "3.0.0",
        "db_engine":    "MySQL 8.0",
        "dependencies": {"sqlalchemy": "2.0", "razorpay": "1.3", "paytm": "2.1"},
    })

@app.route("/docs")
def docs():
    html = """<!DOCTYPE html>
<html><head>
<title>BazaarAPI — Developer Docs</title>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css">
<style>body{margin:0}#header{background:#2874F0;color:#fff;padding:16px 24px;font-family:sans-serif;font-size:20px;font-weight:bold}#sub{background:#FB641B;color:#fff;padding:6px 24px;font-family:sans-serif;font-size:13px}</style>
</head><body>
<div id="header">🛒 BazaarAPI — India Ka Apna Online Bazaar</div>
<div id="sub">Developer API Documentation — v2.1.0 | support@bazaarapi.in</div>
<div id="swagger-ui"></div>
<script>
SwaggerUIBundle({url:"/swagger.json",dom_id:"#swagger-ui",presets:[SwaggerUIBundle.presets.apis,SwaggerUIBundle.SwaggerUIStandalonePreset],layout:"BaseLayout"})
</script></body></html>"""
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print("\n" + "="*65)
    print("  🛒  BazaarAPI — Deliberately Vulnerable Indian Shopping API")
    print("  ⚠️   FOR SECURITY TESTING / FYP DEMO ONLY")
    print("="*65)
    print(f"\n  Running at: http://0.0.0.0:{port}")
    print("\n  OWASP API Vulnerabilities Present:")
    print("    API1  BOLA/IDOR      — /api/v1/users/<id>, /api/v1/orders/<id>")
    print("    API2  Broken Auth    — JWT none, NoSQL bypass, weak secret")
    print("    API3  Mass Assign    — /api/v1/register (role, isAdmin, balance)")
    print("    API3  SQL Injection  — /api/v1/products?search=")
    print("    API4  No Rate Limit  — /api/v1/login, /api/v1/coupon")
    print("    API5  BFLA           — /api/v1/admin/users (no role check)")
    print("    API7  SSRF           — /api/v1/fetch?url=")
    print("    API8  CORS wildcard  — all endpoints")
    print("    API9  Swagger/env    — /swagger.json, /.env exposed")
    print("    GraphQL Introspect  — /graphql")
    print("    XXE                 — /api/v1/import")
    print("="*65)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)