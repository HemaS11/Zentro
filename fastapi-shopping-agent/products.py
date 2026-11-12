"""Mock product catalog (replace with a real Product API later)."""

CATEGORIES = ["Laptops", "Textbooks", "Headphones", "Accessories"]

_ROWS = [
    # id, name, price, category, rating, tags, description
    ("LAP-001", "Acer Aspire 5 (Core i5, 16GB, 512GB SSD)", 44990, "Laptops", 4.2, "windows student",
     "Reliable all-rounder for engineering students: coding, MATLAB and light CAD."),
    ("LAP-002", "HP 15s (Ryzen 5, 8GB, 512GB SSD)", 41990, "Laptops", 4.1, "windows student",
     "Budget engineering laptop with a fast SSD and a full-size keyboard."),
    ("LAP-003", "Lenovo IdeaPad Slim 3 (Core i5, 16GB, 512GB)", 48490, "Laptops", 4.3, "windows slim",
     "Slim, light engineering laptop with 16GB RAM for multitasking and compilers."),
    ("LAP-004", "ASUS Vivobook 15 (Core i7, 16GB, 512GB)", 52990, "Laptops", 4.4, "windows performance",
     "Core i7 power for engineering software, simulations and virtual machines."),
    ("LAP-005", "Dell Inspiron 15 (Ryzen 7, 16GB, 1TB SSD)", 58990, "Laptops", 4.3, "windows storage",
     "Large 1TB storage and Ryzen 7 for engineering projects and datasets."),
    ("LAP-006", "ASUS TUF Gaming F15 (RTX 3050, 16GB)", 67990, "Laptops", 4.4, "windows gaming gpu",
     "Dedicated GPU for engineering simulations, rendering and gaming."),
    ("LAP-007", "Apple MacBook Air M2 (8GB, 256GB)", 89900, "Laptops", 4.8, "macos premium",
     "Premium fanless laptop with all-day battery, great for engineering and design."),
    ("BK-001", "Higher Engineering Mathematics - B.S. Grewal", 699, "Textbooks", 4.5, "mathematics",
     "Standard engineering mathematics text for first and second year courses."),
    ("BK-002", "Digital Design - M. Morris Mano", 560, "Textbooks", 4.4, "electronics digital",
     "Clear introduction to logic design for electronics and computer engineering."),
    ("BK-003", "Fundamentals of Electric Circuits - Alexander & Sadiku", 920, "Textbooks", 4.3, "electrical circuits",
     "Core electrical engineering textbook with solved problems."),
    ("BK-004", "Engineering Mechanics - Beer & Johnston", 1150, "Textbooks", 4.2, "mechanical statics",
     "Statics and dynamics for mechanical and civil engineering students."),
    ("BK-005", "Thermodynamics: An Engineering Approach - Cengel", 1350, "Textbooks", 4.4, "mechanical thermodynamics",
     "Widely used thermodynamics reference for engineering degrees."),
    ("BK-006", "Introduction to Algorithms - Cormen (CLRS)", 1899, "Textbooks", 4.7, "computer science algorithms",
     "The classic computer science and engineering text on algorithms."),
    ("HP-001", "boAt Rockerz 255 Pro+ Wireless Neckband", 1299, "Headphones", 4.1, "wireless neckband bluetooth",
     "Wireless bluetooth earphones with 60-hour battery and fast charging."),
    ("HP-002", "Boult Z40 Wireless Earbuds", 1499, "Headphones", 4.0, "wireless earbuds bluetooth",
     "Wireless earbuds with low-latency mode and quad-mic call noise reduction."),
    ("HP-003", "realme Buds Wireless 3 Neckband", 1799, "Headphones", 4.2, "wireless neckband bluetooth",
     "Wireless neckband with 30dB noise cancellation and deep bass."),
    ("HP-004", "OnePlus Bullets Wireless Z2", 1999, "Headphones", 4.3, "wireless neckband bluetooth",
     "Wireless earphones with 45-hour battery and bass-focused sound."),
    ("HP-005", "Sony WH-CH520 Wireless Headphones", 3990, "Headphones", 4.4, "wireless over-ear bluetooth",
     "Over-ear wireless headphones with 50-hour battery and clear calls."),
    ("HP-006", "JBL Tune 760NC Wireless Headphones", 4999, "Headphones", 4.3, "wireless over-ear noise-cancelling",
     "Over-ear wireless headphones with active noise cancelling."),
    ("AC-001", "Casio fx-991EX Scientific Calculator", 1295, "Accessories", 4.7, "calculator engineering exam",
     "Exam-approved scientific calculator for engineering coursework."),
    ("AC-002", "Logitech M235 Wireless Mouse", 699, "Accessories", 4.3, "wireless mouse",
     "Compact wireless mouse with long battery life."),
    ("AC-003", "Lenovo 15.6-inch Laptop Backpack", 1199, "Accessories", 4.2, "backpack bag student",
     "Water-resistant backpack that fits laptops up to 15.6 inches."),
    ("AC-004", "Redragon K552 Mechanical Keyboard", 2499, "Accessories", 4.4, "keyboard mechanical wired",
     "Compact mechanical keyboard with tactile switches."),
]

CATALOG = [
    {"id": i, "name": n, "price": p, "category": c, "rating": r, "tags": t, "description": d,
     "link": f"https://shop.example.com/{c.lower()}/{i.lower()}"}
    for i, n, p, c, r, t, d in _ROWS
]
