"""Product catalogue. Used to seed DynamoDB (scripts/seed_products.py) and as the
in-memory fallback when the app runs locally without AWS."""

CATEGORY_COLOURS = {
    "Audio": "#7c5cff",
    "Wearables": "#00b894",
    "Accessories": "#e17055",
    "Gadgets": "#0984e3",
}

PRODUCTS = [
    {"product_id": "p-001", "name": "Aura Wireless Earbuds", "category": "Audio", "price_inr": 2499,
     "description": "Compact earbuds with 24-hour battery and a pocket-sized case."},
    {"product_id": "p-002", "name": "Pulse Over-Ear Headphones", "category": "Audio", "price_inr": 3999,
     "description": "Soft ear cushions, deep bass and 40-hour playtime."},
    {"product_id": "p-003", "name": "Bolt Bluetooth Speaker", "category": "Audio", "price_inr": 1799,
     "description": "Splash-proof portable speaker that fills a room."},
    {"product_id": "p-004", "name": "Nova Fitness Band", "category": "Wearables", "price_inr": 1999,
     "description": "Steps, sleep and heart rate on a bright AMOLED display."},
    {"product_id": "p-005", "name": "Orbit Smartwatch", "category": "Wearables", "price_inr": 5499,
     "description": "Calls, notifications and GPS with a 7-day battery."},
    {"product_id": "p-006", "name": "Halo Smart Ring", "category": "Wearables", "price_inr": 6999,
     "description": "Sleep and recovery tracking in a titanium ring."},
    {"product_id": "p-007", "name": "Flux 65W GaN Charger", "category": "Accessories", "price_inr": 1499,
     "description": "One tiny charger for laptop, phone and tablet."},
    {"product_id": "p-008", "name": "Weave Braided USB-C Cable", "category": "Accessories", "price_inr": 499,
     "description": "1.5 m fast-charge cable that survives daily bending."},
    {"product_id": "p-009", "name": "Dock Laptop Stand", "category": "Accessories", "price_inr": 1299,
     "description": "Foldable aluminium stand that lifts your screen to eye level."},
    {"product_id": "p-010", "name": "Glide Wireless Mouse", "category": "Gadgets", "price_inr": 999,
     "description": "Quiet clicks, silent scroll and a six-month battery."},
    {"product_id": "p-011", "name": "Beam Mini Projector", "category": "Gadgets", "price_inr": 8999,
     "description": "Movie night anywhere, with a built-in speaker."},
    {"product_id": "p-012", "name": "Snap Webcam 1080p", "category": "Gadgets", "price_inr": 2299,
     "description": "Sharp video calls with autofocus and a privacy shutter."},
]
