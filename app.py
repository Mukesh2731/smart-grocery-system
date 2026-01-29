from flask import Flask, render_template, request, redirect
from database import connect_db, create_table

app = Flask(__name__)

# create database tables
create_table()


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


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/products", methods=["GET", "POST"])
def manage_products():
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        qty = request.form["qty"]

        cur.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
            (name, price, qty)
        )
        conn.commit()

    cur.execute("SELECT id, name, price, quantity FROM products")
    rows = cur.fetchall()
    conn.close()

    products = []
    for r in rows:
        products.append({
            "id": r[0],
            "name": r[1],
            "price": r[2],
            "qty": r[3]
        })

    return render_template("products.html", products=products)


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

        cur.execute("SELECT price, quantity FROM products WHERE id=?", (pid,))
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


if __name__ == "__main__":
    app.run(debug=True)
