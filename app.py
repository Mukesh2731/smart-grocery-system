from flask import Flask, render_template, request, redirect
from database import connect_db, create_table

app = Flask(__name__)
create_table()


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid login")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM products WHERE quantity < 5")
    low_stock = cur.fetchone()[0]

    cur.execute("SELECT SUM(total) FROM sales")
    total_sales = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM sales")
    total_orders = cur.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        low_stock=low_stock,
        total_sales=total_sales,
        total_orders=total_orders
    )


@app.route("/products", methods=["GET", "POST"])
def products():
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
            (request.form["name"], request.form["price"], request.form["qty"])
        )
        conn.commit()

    cur.execute("SELECT id, name, price, quantity FROM products")
    rows = cur.fetchall()
    conn.close()

    products = [{"id": r[0], "name": r[1], "price": r[2], "qty": r[3]} for r in rows]
    return render_template("products.html", products=products)


@app.route("/edit/<int:pid>", methods=["GET", "POST"])
def edit_product(pid):
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            "UPDATE products SET price=?, quantity=? WHERE id=?",
            (request.form["price"], request.form["qty"], pid)
        )
        conn.commit()
        conn.close()
        return redirect("/products")

    cur.execute("SELECT name, price, quantity FROM products WHERE id=?", (pid,))
    p = cur.fetchone()
    conn.close()

    return render_template(
        "edit_product.html",
        product={"name": p[0], "price": p[1], "qty": p[2]}
    )


@app.route("/billing", methods=["GET", "POST"])
def billing():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT id, name, price, quantity FROM products")
    items = cur.fetchall()

    bill = None
    error = None

    if request.method == "POST":
        pid = int(request.form["product_id"])
        qty = int(request.form["qty"])

        cur.execute("SELECT name, price, quantity FROM products WHERE id=?", (pid,))
        product = cur.fetchone()

        if product and product[2] >= qty:
            total = product[1] * qty

            cur.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id=?",
                (qty, pid)
            )
            cur.execute(
                "INSERT INTO sales (product_id, quantity, total) VALUES (?, ?, ?)",
                (pid, qty, total)
            )
            conn.commit()

            bill = {
                "name": product[0],
                "price": product[1],
                "qty": qty,
                "total": total
            }
        else:
            error = "Insufficient stock"

    conn.close()

    products = [{"id": p[0], "name": p[1], "price": p[2], "quantity": p[3]} for p in items]
    return render_template("billing.html", products=products, bill=bill, error=error)


@app.route("/report")
def report():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT sales.id, products.name, sales.quantity, sales.total
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.id DESC
    """)
    sales = cur.fetchall()

    cur.execute("SELECT SUM(total) FROM sales")
    total_sales = cur.fetchone()[0] or 0

    conn.close()

    return render_template("report.html", sales=sales, total_sales=total_sales)


if __name__ == "__main__":
    app.run(debug=True)
