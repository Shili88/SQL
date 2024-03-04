from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import flash
from flask import url_for
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy()
db.init_app(app)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction = db.Column(db.Integer, nullable=False)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(80), default=datetime.now().strftime("%Y-%m-%d"))
    content = db.Column(db.String(200), nullable=False)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(120), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
@app.route("/index", methods=["get", "post"])
def index ():
    transaction = db.session.query(Account).first()
    inventory = db.session.query(Inventory).all()
    return render_template ("index.html", title="Main Page!", account = transaction, inventory=inventory)


@app.route("/balance", methods=["get", "post"])
def balance ():
    if request.method == "POST":
        account = db.session.query(Account).first()

        if not account:
            account = Account(transaction = 0)

        transaction =  int(request.form["amount"])
        balance_action = request.form["balance_action"]

        if balance_action == "add":
            account.transaction += transaction 
            flash(f"Successfully added to the account")
        elif balance_action == "subtract":
            if account.transaction >= balance:
                flash("Not enough the money to subtract")
            else: 
                Account.transaction -= transaction 
                flash(f"Successfully dedcuted from the account")   

        new_history = History(date=datetime.now().strftime("%Y-%M-%D"), content=f"{balance_action} {transaction}  euros to the account balance")
  
        db.session.add(account)
        db.session.add(new_history)
        db.session.commit()

        return redirect(url_for("index"))
    return render_template ("balance.html", balance=balance)


@app.route("/purchase/", methods=["get", "post"])
def purchase ():
    if request.method == "POST":
        item_name = request.form["item_name"]
        item_quantity = int(request.form["item_quantity"])
        item_price = int(request.form["item_price"])
        purchase = item_quantity * item_price

        account = db.session.query(Account).first()
        inventory = db.session.query(Inventory).filter_by(item=item_name).first()
    
        if account.transaction >= purchase:
            account.transaction -= purchase

            if inventory:
                inventory.stock += item_quantity
            else:
                inventory = Inventory(item=item_name, stock=item_quantity, price=item_price)
                db.session.add(inventory)

                new_history = History(content=f"Purchased {item_name} for {purchase} euros ({item_quantity} units)")
                db.session.add(account)
                db.session.add(new_history)
                db.session.commit()
                flash(f"Bought {item_name} ({item_quantity} units) for a total cost of {purchase}")
        else:
            flash("Insufficient account balance!")

        return redirect(url_for("index"))
    return render_template ("purchase.html")


@app.route("/sale", methods=["get", "post"])
def sale ():
    if request.method == "POST":
        item_name = request.form["item_name"]
        item_quantity = int(request.form["item_quantity"])
        item_price = int(request.form["item_price"])
        sale = int(item_quantity * item_price)

        account = db.session.query(Account).first()
        inventory = db.session.query(Inventory).filter(Inventory.item == item_name).first()

        if inventory:
            if inventory.stock >= item_quantity:
                inventory.stock -= item_quantity
                account.transaction += sale

                new_history = History(content=f"Sold {item_name} for {sale} euros ({item_quantity} units)")

                db.session.add(inventory)
                db.session.add(account)
                db.session.add(new_history)
                db.session.commit()

                flash(f"Sold {item_name} ({item_quantity} units) for a total amount of {sale} euros successfully!")
            else:
                flash(f"Insufficient stock of {item_name} for sale.")
        else:
            flash(f"The item {item_name} is currently not available.")

        return redirect(url_for("index"))
    return render_template ("sale.html")

@app.route("/history", methods=["get", "post"])
def history():
    history = db.session.query(History).all()
    return render_template("history.html", history = history)

if __name__ == "__main__":
    app.run(debug=True)