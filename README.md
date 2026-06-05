# BazaarAPI 🛒
### India Ka Apna Vulnerable Shopping API

A **deliberately vulnerable** Indian e-commerce REST API built for API security testing and FYP demonstrations.

> ⚠️ **FOR SECURITY TESTING / FYP DEMO ONLY — DO NOT USE IN PRODUCTION**

---

## Live Demo
`https://bazaarapi.onrender.com`

## Swagger Docs
`https://bazaarapi.onrender.com/docs`

---

## Vulnerabilities Covered (OWASP API Top 10 — 2023)

| ID | Vulnerability | Endpoint |
|----|--------------|----------|
| API1 | BOLA / IDOR | `/api/v1/users/<id>`, `/api/v1/orders/<id>` |
| API2 | Broken Auth — JWT alg:none, NoSQL bypass | `/api/v1/login` |
| API3 | Mass Assignment | `/api/v1/register` |
| API3 | SQL Injection | `/api/v1/products?search=` |
| API4 | No Rate Limiting | `/api/v1/login`, `/api/v1/coupon` |
| API5 | BFLA — Admin access without role check | `/api/v1/admin/users` |
| API7 | SSRF | `/api/v1/fetch?url=` |
| API8 | CORS wildcard + missing headers | All endpoints |
| API9 | Swagger + .env exposed | `/swagger.json`, `/.env` |
| API10 | GraphQL introspection | `/graphql` |

---

## Run Locally

```bash
pip install -r requirements.txt
python vulnshop_api.py
# API running at http://localhost:5001
```

## Deploy on Render (Free)

1. Fork this repo
2. Go to [render.com](https://render.com) → New Web Service
3. Connect this repo
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn --bind 0.0.0.0:$PORT --workers 2 vulnshop_api:app`
6. Deploy!

---

## Test Credentials

| User | Username | Password | Role |
|------|----------|----------|------|
| Admin | `arjun_admin` | `admin@123` | admin |
| User | `priya_patel` | `priya123` | user |
| User | `ravi_kumar` | `password` | user |
| Seller | `meera_iyer` | `meera@456` | seller |

---

## Scan with OWASP CyberHawk

```bash
python -m backend.cli scan https://bazaarapi.onrender.com
```

---

*Built for OWASP CyberHawk FYP Demo — Lahore Garrison University*
