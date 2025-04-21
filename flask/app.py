import os
import math
import mysql.connector
from flask import Flask, render_template, flash, request, redirect, url_for
from dotenv import load_dotenv

PAGE_SIZE = 50
UPLOAD_FOLDER = 'static/uploads'
TABLES_TO_MANAGE = ['recipe', 'ingredient', 'unit', 'step']

load_dotenv(override=True)

app = Flask(__name__)

def get_db_connection():
    conn = mysql.connector.connect(
        user = os.environ["MYSQL_USER"],
        password = os.environ["MYSQL_PASS"],
        host = os.getenv("MYSQL_HOST", "localhost"),
        port = os.getenv("MYSQL_PORT", "3306"),
        database = os.environ["MYSQL_DATABASE"]
    )
    return conn

def error_response(error_text):
    return render_template('error.html', error_text=error_text)

CUSTOMER_QUERY_HDR = """
    SELECT c.customer_id, c.age, c.gender, c.subscription_status, c.previous_purchases,
           pm.payment_method, f.frequency_name, l.location_name
    FROM customer c
    INNER JOIN payment_method pm ON c.preferred_payment_method_id = pm.payment_method_id
    INNER JOIN frequency f ON c.frequency_of_purchases_id = f.frequency_id
    INNER JOIN location l ON c.location_id = l.location_id
"""

PURCHASE_QUERY_HDR = """
    SELECT p.purchase_id, p.customer_id, i.item_purchased, cat.category_name, i.size, i.color, p.purchase_amount, s.season_name,
           p.review_rating, pm.payment_method, st.shipping_type_name, p.discount_applied, p.promo_code_used
    FROM purchase p
    INNER JOIN payment_method pm ON p.payment_method_id = pm.payment_method_id
    INNER JOIN item i ON p.item_id = i.item_id
    INNER JOIN category cat ON i.category_id = cat.category_id
    INNER JOIN season s ON p.season_id = s.season_id
    INNER JOIN shipping_type st ON p.shipping_type_id = st.shipping_type_id
"""

@app.route('/customer/')
@app.route('/customer/<int:id>')
def customer(id=None):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            if id is None:
                page = request.args.get('page', default=1, type=int)
                cur.execute(f"{CUSTOMER_QUERY_HDR} ORDER BY c.customer_id LIMIT {PAGE_SIZE} OFFSET {(page - 1) * PAGE_SIZE};")
                customers = cur.fetchall()
                cur.execute("SELECT COUNT(*) AS count FROM customer;")
                total_count = cur.fetchone()['count']
                return render_template('index.html', customers=customers, page_name='index', page=page, total_count=total_count,
                                       max=max, min=min, ceil=math.ceil)
            else:
                cur.execute(f"{CUSTOMER_QUERY_HDR} WHERE c.customer_id = %s;", (id,))
                customer = cur.fetchone()
                cur.execute(f"{PURCHASE_QUERY_HDR} WHERE p.customer_id = %s;", (id,))
                purchases = cur.fetchall()
                return render_template('customer.html', customer=customer, purchases=purchases)

@app.route('/')
def index():
    page = request.args.get('page', default=1, type=int)
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(f"{CUSTOMER_QUERY_HDR} ORDER BY c.customer_id LIMIT {PAGE_SIZE} OFFSET {(page - 1) * PAGE_SIZE};")
            customers = cur.fetchall()
            cur.execute("SELECT COUNT(*) AS count FROM customer;")
            total_count = cur.fetchone()['count']

    return render_template('index.html', customers=customers, page_name='index', page=page, total_count=total_count,
                           max=max, min=min, ceil=math.ceil)



@app.route('/purchase/')
@app.route('/purchase/<int:id>')
def purchase(id=None):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            if id is None:
                page = request.args.get('page', default=1, type=int)
                cur.execute(f"{PURCHASE_QUERY_HDR} ORDER BY p.purchase_id LIMIT {PAGE_SIZE} OFFSET {(page - 1) * PAGE_SIZE};")
                purchases = cur.fetchall()
                cur.execute("SELECT COUNT(*) AS count FROM purchase;")
                total_count = cur.fetchone()['count']
                return render_template('purchases.html', purchases=purchases, page_name='purchase', page=page,
                                       total_count=total_count, max=max, min=min, ceil=math.ceil)
            else:
                cur.execute(f"{PURCHASE_QUERY_HDR} WHERE p.purchase_id = %s;", (id,))
                purchases = cur.fetchone()
                return render_template('purchase.html', purchase=purchases)


@app.route('/purchases/<int:id>')
def purchases(id=None):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            page = request.args.get('page', default=1, type=int)
            if id is None:
                cur.execute(f"{PURCHASE_QUERY_HDR} ORDER BY p.purchase_id LIMIT {PAGE_SIZE} OFFSET {(page - 1) * PAGE_SIZE};")
                purchases = cur.fetchall()
                cur.execute("SELECT COUNT(*) AS count FROM purchase;")
                total_count = cur.fetchone()['count']
                return render_template('purchases.html', purchases=purchases, page_name='purchase', page=page,
                                       total_count=total_count, max=max, min=min, ceil=math.ceil)
            else:
                cur.execute(f"{PURCHASE_QUERY_HDR} WHERE p.customer_id = %s;", (id,))
                purchases = cur.fetchall()
                total_count = len(purchases)
                return render_template('purchases.html', purchases=purchases, total_count=total_count, page_name='purchase',
                                       page=page, max=max, min=min, ceil=math.ceil)

SIMPLE_CUSTOMER_QUERY_HDR = """
    SELECT customer_id, age, gender, location_id, subscription_status,
           previous_purchases, preferred_payment_method_id, frequency_of_purchases_id
    FROM customer
"""

@app.route('/edit_customer/')
@app.route('/edit_customer/<int:id>')
def edit_customer(id=None):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            customer = None
            if id is not None:
                cur.execute(f"{SIMPLE_CUSTOMER_QUERY_HDR} WHERE customer_id = %s;", (id,))
                customer = cur.fetchone()
                if customer is None:
                    flash('Customer not found.')
                    return redirect(url_for('index', max=max, min=min, ceil=math.ceil))
            cur.execute("SELECT location_id, location_name FROM location;")
            locations = cur.fetchall()
            cur.execute("SELECT payment_method_id, payment_method FROM payment_method;")
            payment_methods = cur.fetchall()
            cur.execute("SELECT frequency_id, frequency_name FROM frequency;")
            frequencies = cur.fetchall()
            return render_template('edit_customer.html', customer=customer, locations=locations,
                                   payment_methods=payment_methods, frequencies=frequencies)

@app.route('/update_customer/', methods=['POST'])
@app.route('/update_customer/<int:id>', methods=['POST'])
def update_customer(id=None):
    age = request.form['age']
    gender = request.form['gender']
    location_id = request.form['location']
    subscription_status = request.form['subscription_status']
    previous_purchases = request.form['previous_purchases']
    preferred_payment_method_id = request.form['payment_method']
    frequency_of_purchases_id = request.form['frequency']
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if id is not None:
                cur.execute("""
                UPDATE customer
                SET age = %s, gender = %s, location_id = %s, subscription_status = %s, previous_purchases = %s,
                preferred_payment_method_id = %s, frequency_of_purchases_id = %s
                WHERE customer_id = %s;
                """, (age, gender, location_id, subscription_status, previous_purchases,
                      preferred_payment_method_id, frequency_of_purchases_id, id))
                conn.commit()
            else:
                cur.execute("SELECT MAX(customer_id) FROM customer;")
                if row := cur.fetchone():
                    id = row[0] + 1
                else:
                    id = 1
                cur.execute("""
                INSERT INTO customer (customer_id, age, gender, location_id, subscription_status, previous_purchases,
                                     preferred_payment_method_id, frequency_of_purchases_id) VALUES
                   (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (id, age, gender, location_id, subscription_status, previous_purchases,
                      preferred_payment_method_id, frequency_of_purchases_id))
                conn.commit()
    return redirect(url_for('customer', id=id))

@app.route('/delete_customer/<int:id>', methods=['GET'])
def delete_customer(id=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if id is not None:
                cur.execute("DELETE FROM customer WHERE customer_id = %s;", (id,))
                conn.commit()
            else:
                flash('Customer not found.')
    return redirect(url_for('index'))


SIMPLE_PURCHASE_QUERY_HDR = """
    SELECT purchase_id, item_id, customer_id, purchase_amount, season_id,
           review_rating, payment_method_id, shipping_type_id, discount_applied, promo_code_used
    FROM purchase
"""

@app.route('/edit_purchase/')
@app.route('/edit_purchase/<int:id>')
def edit_purchase(id=None):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            purchase = None
            if id is not None:
                cur.execute(f"{SIMPLE_PURCHASE_QUERY_HDR} WHERE purchase_id = %s;", (id,))
                purchase = cur.fetchone()
                if purchase is None:
                    flash('Purchase not found.')
                    return redirect(url_for('index', max=max, min=min, ceil=math.ceil))
            cur.execute("SELECT item_id, item_purchased, size, color FROM item;")
            items = cur.fetchall()
            cur.execute("SELECT season_id, season_name FROM season;")
            seasons = cur.fetchall()
            cur.execute("SELECT payment_method_id, payment_method FROM payment_method;")
            payment_methods = cur.fetchall()
            cur.execute("SELECT shipping_type_id, shipping_type_name FROM shipping_type;")
            shipping_types = cur.fetchall()
            return render_template('edit_purchase.html', purchase=purchase, items=items, seasons=seasons,
                                   payment_methods=payment_methods, shipping_types=shipping_types)


@app.route('/update_purchase/', methods=['POST'])
@app.route('/update_purchase/<int:id>', methods=['POST'])
def update_purchase(id=None):
    item = request.form['item']
    customer_id = request.form['customer_id']
    purchase_amount = request.form['purchase_amount']
    season_id = request.form['season_id']
    review_rating = request.form['review_rating']
    payment_method_id = request.form['payment_method_id']
    shipping_type_id = request.form['shipping_type_id']
    discount_applied = request.form['discount_applied']
    promo_code_used = request.form['promo_code_used']

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if id is not None:
                cur.execute("""
                UPDATE purchase
                SET item_id = %s, customer_id = %s, purchase_amount = %s, season_id = %s,
                review_rating = %s, payment_method_id = %s, shipping_type_id = %s,
                discount_applied = %s, promo_code_used = %s
                WHERE purchase_id = %s;
                """, (item, customer_id, purchase_amount, season_id, review_rating,
                      payment_method_id, shipping_type_id, discount_applied, promo_code_used, id))
                conn.commit()
            else:
                cur.execute("SELECT MAX(purchase_id) FROM purchase;")
                if row := cur.fetchone():
                    id = row[0] + 1
                else:
                    id = 1
                cur.execute("""
                INSERT INTO purchase (purchase_id, item_id, customer_id, purchase_amount, season_id,
                                      review_rating, payment_method_id, shipping_type_id,
                                      discount_applied, promo_code_used) VALUES
                   (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (id, item, customer_id, purchase_amount, season_id, review_rating,
                      payment_method_id, shipping_type_id, discount_applied, promo_code_used))
                conn.commit()
    return redirect(url_for('purchase', id=id))


@app.route('/delete_purchase/<int:id>', methods=['GET'])
def delete_purchase(id=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if id is not None:
                try:
                    cur.execute("DELETE FROM purchase WHERE purchase_id = %s;", (id,))
                    conn.commit()
                except mysql.connector.Error as err:
                    if err.errno == 1451:
                        return error_response('Cannot delete purchase. It is referenced by other records.')
                    else:
                        return error_response(f'Error: {err}')
            else:
                return error_response('Purchase not found.')
    return redirect(url_for('purchase'))


ITEM_QUERY_HDR = """
    SELECT i.item_id, i.item_purchased, i.category_id, c.category_name, i.size, i.color
    FROM item i INNER JOIN category c ON i.category_id = c.category_id
"""

@app.route('/item/')
@app.route('/item/<int:id>')
def item(id=None):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            if id is None:
                page = request.args.get('page', default=1, type=int)
                cur.execute(f"{ITEM_QUERY_HDR} ORDER BY i.item_id LIMIT {PAGE_SIZE} OFFSET {(page - 1) * PAGE_SIZE};")
                items = cur.fetchall()
                cur.execute("SELECT COUNT(*) AS count FROM item;")
                total_count = cur.fetchone()['count']
                return render_template('items.html', items=items, page_name='item', page=page,
                                       total_count=total_count, max=max, min=min, ceil=math.ceil)
            else:
                cur.execute(f"{ITEM_QUERY_HDR} WHERE i.item_id = %s;", (id,))
                item = cur.fetchone()
                return render_template('item.html', item=item)


@app.route('/edit_item/')
@app.route('/edit_item/<int:id>')
def edit_item(id=None):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            item = None
            if id is not None:
                cur.execute(f"{ITEM_QUERY_HDR} WHERE item_id = %s;", (id,))
                item = cur.fetchone()
                if item is None:
                    flash('Item not found.')
                    return redirect(url_for('items.html', max=max, min=min, ceil=math.ceil))
            cur.execute("SELECT category_id, category_name FROM category;")
            categories = cur.fetchall()
            return render_template('edit_item.html', item=item, categories=categories)


@app.route('/update_item/', methods=['POST'])
@app.route('/update_item/<int:id>', methods=['POST'])
def update_item(id=None):
    item_purchased = request.form['item_purchased']
    category_id = request.form['category_id']
    size = request.form['size']
    color = request.form['color']

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if id is not None:
                cur.execute("""
                UPDATE item
                SET item_purchased = %s, category_id = %s, size = %s, color = %s
                WHERE item_id = %s;
                """, (item_purchased, category_id, size, color, id))
                conn.commit()
            else:
                cur.execute("SELECT MAX(item_id) FROM item;")
                if row := cur.fetchone():
                    id = row[0] + 1
                else:
                    id = 1
                cur.execute("""
                INSERT INTO item (item_id, item_purchased, category_id, size, color) VALUES
                   (%s, %s, %s, %s, %s);
                """, (id, item_purchased, category_id, size, color))
                conn.commit()
    return redirect(url_for('item', id=id))

@app.route('/delete_item/<int:id>', methods=['GET'])
def delete_item(id=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if id is not None:
                try:
                    cur.execute("DELETE FROM item WHERE item_id = %s;", (id,))
                    conn.commit()
                except mysql.connector.Error as err:
                    if err.errno == 1451:
                        return error_response('Cannot delete item. It is referenced by other records.')
                    else:
                        return error_response(f'Error: {err}')
            else:
                return error_response('Item not found.')
    return redirect(url_for('item'))

