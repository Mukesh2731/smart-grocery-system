from flask import Flask, render_template, request, redirect
from database import connect_db, create_table

app = Flask(__name__)

# Ensure DB & tables are created on startup
create_table()


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/products", methods=["GET", "POST"])
def products():
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO products
            (name, brand, category, weight, price, mrp, image, quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["name"],
            request.form["brand"],
            request.form["category"],
            request.form["weight"],
            request.form["price"],
            request.form["mrp"],
            request.form["image"],
            request.form["qty"]
        ))
        conn.commit()

    cur.execute("""
        SELECT name, brand, category, weight, price, mrp, quantity
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
            "qty": r[6]
        })

    return render_template("products.html", products=products)


if __name__ == "__main__":
    app.run(debug=True)
