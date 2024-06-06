from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()



class Gem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255))  # or image_url = db.Column(db.Text)
    added_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    sold = db.Column(db.Boolean, default=False)
    
    def __init__(self, name, type, quantity, weight, price, image_filename, sold):
        self.name = name
        self.type = type
        self.quantity = quantity
        self.weight = weight
        self.price = price
        self.image_filename = image_filename
        self.sold = sold
    
class Middleman(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    contact_info = db.Column(db.String(120), nullable=False)
    
    borrowed_gems = db.relationship('BorrowedGem', backref='middleman', cascade='all, delete-orphan', passive_deletes=True)

    

    def __init__(self, name, contact_info):
        self.name = name
        self.contact_info = contact_info

class BorrowedGem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gem_id = db.Column(db.Integer, db.ForeignKey('gem.id'), nullable=False)
    middleman_id = db.Column(db.Integer, db.ForeignKey('middleman.id', ondelete='CASCADE'), nullable=False)
    date_borrowed = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='borrowed')  # 'borrowed', 'returned', 'sold'
    date_returned_or_sold = db.Column(db.Date, nullable=True)

    gem = db.relationship('Gem', backref=db.backref('borrowed_gems', lazy=True))

    def __init__(self, gem_id, middleman_id, date_borrowed):
        self.gem_id = gem_id
        self.middleman_id = middleman_id
        self.date_borrowed = date_borrowed

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gem_id = db.Column(db.Integer, db.ForeignKey('gem.id'), nullable=False)
    date_sold = db.Column(db.Date, nullable=False)
    sold_price = db.Column(db.Float, nullable=False)
    bought_price = db.Column(db.Float, nullable=False)

    gem = db.relationship('Gem', backref=db.backref('transactions', lazy=True))
    

    def __init__(self, gem_id, date_sold, sold_price, bought_price):
        self.gem_id = gem_id
        self.date_sold = date_sold
        self.sold_price = sold_price
        self.bought_price = bought_price

