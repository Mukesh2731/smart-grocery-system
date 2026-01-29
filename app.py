from flask import Flask, render_template, request, redirect
from database import connect_db, create_table

app = Flask(__name__)

# create database tables
create_table()


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid login")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ---------------- ADD / VIEW PRODUCTS (ADMIN) ----------------
@app.route("/products", methods=["GET", "POST"])
def products():
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        brand = request.form["brand"]
        category = request.form["category"]
        weight = request.form["weight"]
        price = request.form["price"]
        mrp = request.form["mrp"]
        qty = request.form["qty"]
        image = request.form["image"]

        cur.execute(
            """
            INSERT INTO products
            (name, brand, category, weight, price, mrp, image, quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, brand, category, weight, price, mrp, image, qty)
        )
        conn.commit()

    cur.execute("""
        SELECT id, name, brand, category, weight, price, mrp, image, quantity
        FROM products
    """)
    rows = cur.fetchall()
    conn.close()

    products = []
    for r in rows:
        products.append({
            "id": r[0],
            "name": r[1],
            "brand": r[2],
            "category": r[3],
            "weight": r[4],
            "price": r[5],
            "mrp": r[6],
            "image": r[7],
            "qty": r[8]
        })

    return render_template("products.html", products=products)


# ---------------- STORE PAGE (JIOMART STYLE) ----------------
@app.route("/store")
def store():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, brand, category, weight, price, mrp, image, quantity
        FROM products
    """)
    rows = cur.fetchall()
    conn.close()

    products = []
    for r in rows:
        products.append({
            "name": r[0],
            "brand": r[1],
            "category": r[2],
            "weight": r[3],
            "price": r[4],
            "mrp": r[5],
            "image": r[6],
            "quantity": r[7]
        })

    return render_template("store.html", products=products)


# ---------------- BILLING ----------------
@app.route("/billing", methods=["GET", "POST"])
def billing():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT id, name, price, quantity FROM products")
    rows = cur.fetchall()

    products = []
    for r in rows:
        products.append({
            "id": r[0],
            "name": r[1],
            "price": r[2],
            "quantity": r[3]
        })

    bill = None
    error = None

    if request.method == "POST":
        pid = int(request.form["product_id"])
        qty = int(request.form["qty"])

        cur.execute(
            "SELECT price, quantity FROM products WHERE id=?",
            (pid,)
        )
        product = cur.fetchone()

        if product and product[1] >= qty:
            bill = product[0] * qty

            # update stock
            cur.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id=?",
                (qty, pid)
            )

            # save sale
            cur.execute(
                "INSERT INTO sales (product_id, quantity, total) VALUES (?, ?, ?)",
                (pid, qty, bill)
            )

            conn.commit()
        else:
            error = "Insufficient stock"

    conn.close()

    return render_template(
        "billing.html",
        products=products,
        bill=bill,
        error=error
    )


# ---------------- SALES REPORT ----------------
@app.route("/report")
def report():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT SUM(total) FROM sales")
    total = cur.fetchone()[0]

    conn.close()

    if total is None:
        total = 0

    return render_template("report.html", total=total)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
