from flask import Flask, render_template, request, redirect
from database import connect_db, create_table
from datetime import datetime

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

    cur.execute("SELECT SUM(profit) FROM sales")
    total_profit = cur.fetchone()[0] or 0

    conn.close()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        low_stock=low_stock,
        total_sales=total_sales,
        total_profit=total_profit
    )


@app.route("/products", methods=["GET", "POST"])
def products():
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            "INSERT INTO products (name, cost_price, sell_price, quantity) VALUES (?, ?, ?, ?)",
            (
                request.form["name"],
                request.form["cost"],
                request.form["price"],
                request.form["qty"]
            )
        )
        conn.commit()

    cur.execute("SELECT id, name, cost_price, sell_price, quantity FROM products")
    rows = cur.fetchall()
    conn.close()

    products = [{
        "id": r[0],
        "name": r[1],
        "cost": r[2],
        "price": r[3],
        "qty": r[4]
    } for r in rows]

    return render_template("products.html", products=products)


@app.route("/edit/<int:pid>", methods=["GET", "POST"])
def edit_product(pid):
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            "UPDATE products SET cost_price=?, sell_price=?, quantity=? WHERE id=?",
            (request.form["cost"], request.form["price"], request.form["qty"], pid)
        )
        conn.commit()
        conn.close()
        return redirect("/products")

    cur.execute("SELECT name, cost_price, sell_price, quantity FROM products WHERE id=?", (pid,))
    p = cur.fetchone()
    conn.close()

    return render_template(
        "edit_product.html",
        product={"name": p[0], "cost": p[1], "price": p[2], "qty": p[3]}
    )


@app.route("/billing", methods=["GET", "POST"])
def billing():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT id, name, cost_price, sell_price, quantity FROM products")
    items = cur.fetchall()

    bill = None
    error = None

    if request.method == "POST":
        pid = int(request.form["product_id"])
        qty = int(request.form["qty"])
        customer = request.form["customer"]

        cur.execute(
            "SELECT name, cost_price, sell_price, quantity FROM products WHERE id=?",
            (pid,)
        )
        product = cur.fetchone()

        if product and product[3] >= qty:
            name, cost, price, stock = product
            subtotal = price * qty

            # GST RULE
            if subtotal > 1000:
                cgst = subtotal * 0.03
                sgst = subtotal * 0.03
            else:
                cgst = sgst = 0

            total = subtotal + cgst + sgst
            profit = (price - cost) * qty

            cur.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id=?",
                (qty, pid)
            )

            cur.execute("SELECT MAX(invoice_no) FROM sales")
            last_invoice = cur.fetchone()[0]
            invoice_no = 1 if last_invoice is None else last_invoice + 1

            cur.execute(
                """INSERT INTO sales
                (invoice_no, product_name, qty, subtotal, cgst, sgst, total, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (invoice_no, name, qty, subtotal, cgst, sgst, total, profit)
            )

            conn.commit()

            bill = {
                "invoice": invoice_no,
                "date": datetime.now().strftime("%d-%m-%Y"),
                "customer": customer,
                "name": name,
                "qty": qty,
                "price": price,
                "subtotal": subtotal,
                "cgst": cgst,
                "sgst": sgst,
                "total": total
            }
        else:
            error = "Insufficient stock"

    conn.close()

    products = [{
        "id": p[0],
        "name": p[1],
        "price": p[3],
        "quantity": p[4]
    } for p in items]

    return render_template("billing.html", products=products, bill=bill, error=error)


@app.route("/report")
def report():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT invoice_no, product_name, qty, subtotal, cgst, sgst, total, profit
        FROM sales ORDER BY invoice_no DESC
    """)
    sales = cur.fetchall()
    conn.close()

    return render_template("report.html", sales=sales)


if __name__ == "__main__":
    app.run(debug=True)
