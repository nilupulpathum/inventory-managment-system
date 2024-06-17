from flask import Flask, abort, make_response, render_template, redirect, url_for, request, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from models import db, Gem, Middleman, BorrowedGem, Transaction
from forms import LoginForm, RegistrationForm
import io
import pdfkit
import tempfile



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
app.secret_key = 'supersecretkey'

db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

#-----------------------------------------------------FLASK APP---------------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Create an instance of LoginForm
    if form.validate_on_submit():  # Validate the form submission
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created for {}!'.format(form.username.data), 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        filter_type = request.form.get('filter_type_inventory')
        min_price = request.form.get('min_price_inventory')
        max_price = request.form.get('max_price_inventory')
        min_weight = request.form.get('min_weight_inventory')
        max_weight = request.form.get('max_weight_inventory')
        borrow_status = request.form.get('filter_status_borrowed')
        min_price_transaction = request.form.get('min_price_transaction')
        max_price_transaction = request.form.get('max_price_transaction')
        
        query = Gem.query
        transactions_query = Transaction.query
        borrow_gem_query = BorrowedGem.query
        
        if filter_type:
            query = query.filter_by(type=filter_type, sold=False)
        
        if min_price:
            query = query.filter(Gem.price >= float(min_price), Gem.sold==False)
        
        if max_price:
            query = query.filter(Gem.price <= float(max_price), Gem.sold==False)
        if min_weight:
            query = query.filter(Gem.weight >= float(min_weight), Gem.sold==False)
        
        if max_weight:
            query = query.filter(Gem.weight <= float(max_weight), Gem.sold==False)
        
        gems = query.filter_by(sold=False).all()
        
        if borrow_status:
            borrow_gem_query = borrow_gem_query.filter_by(status=borrow_status).all()
        borrowed_gems = borrow_gem_query.all()
            
        if min_price_transaction:
            transactions_query = Transaction.query.filter(Transaction.sold_price >= float(min_price_transaction))
        
        if max_price_transaction:
            transactions_query = transactions_query.filter(Transaction.sold_price <= float(max_price_transaction))
            
        transactions = transactions_query.all()
            
    else:
        gems = Gem.query.filter_by(sold=False, borrowed = False).all()
        borrowed_gems = BorrowedGem.query.all()
        transactions = Transaction.query.all()
    
    # Get all distinct gem types for the filter
    total_stock = db.session.query(db.func.sum(Gem.price)).filter(Gem.sold == False).scalar() or 0
    sales_made = db.session.query(db.func.sum(Transaction.sold_price)).scalar() or 0
    profit_made = sales_made - (db.session.query(db.func.sum(Gem.price)).join(Transaction, Gem.id == Transaction.gem_id).scalar() or 0)
    gem_types = db.session.query(Gem.type).distinct().all()
    
    middlemen = Middleman.query.all()
    return render_template('dashboard.html',
                           gems=gems, gem_types=[t[0] for t in gem_types],
                           transactions=transactions,
                           middlemen=middlemen,
                           borrowed_gems=borrowed_gems,
                           total_stock=total_stock,
                           sales_made=sales_made,
                           profit_made=profit_made)


@app.route('/add_gem', methods=['GET', 'POST'])
@login_required
def add_gem():
    if request.method == 'POST':
        name = request.form.get('name')
        gem_type = request.form.get('type')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        weight= request.form.get('weight')
        sold = False

        # Handle image upload
        filename = 'placeholder.jpg'
        if 'image' in request.files:
            image = request.files['image']
            if image.filename == '':
                filename = 'placeholder.jpg'
            elif image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Ensure the upload directory exists
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    print(f"Creating directory: {app.config['UPLOAD_FOLDER']}")
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                print(f"Saving image to: {upload_path}")
                image.save(upload_path)
            else:
                flash('Invalid file format', 'danger')
                return redirect(request.url)
        
        new_gem = Gem( name=name, type=gem_type, quantity=quantity, price=price, weight=weight, image_filename=filename, sold=sold)
        db.session.add(new_gem)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_gem.html')

@app.route('/update_gem/<id>', methods=['GET', 'POST'])
@login_required
def update_gem(id):
    gem = Gem.query.get_or_404(id)
    if request.method == 'POST':
        gem.name = request.form.get('name')
        gem.type = request.form.get('type')
        gem.quantity = request.form.get('quantity')
        gem.price = request.form.get('price')
        gem.weight = request.form.get('weight')
        gem.description = request.form.get('description')
        if 'image' in request.files:
            image = request.files['image']
            
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Ensure the upload directory exists
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    print(f"Creating directory: {app.config['UPLOAD_FOLDER']}")
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                print(f"Saving image to: {upload_path}")
                image.save(upload_path)
        else:
            flash('Invalid file format', 'danger')
            return redirect(request.url)  
        gem.image_filename = filename    
        db.session.commit()
        print(gem.image_filename)
        return redirect(url_for('dashboard'))
    return render_template('update_gem.html', gem=gem)

@app.route('/delete_gem/<id>', methods=['GET'])
def delete_gem(id):
    gem = Gem.query.get_or_404(id)
    db.session.delete(gem)
    db.session.commit()
    flash('Gem deleted successfully!')
    return redirect(url_for('dashboard'))



@app.route('/borrow_gem', methods=['GET', 'POST'])
def borrow_gem():
    gems = Gem.query.filter_by(sold=False, borrowed=False)
    middlemen = Middleman.query.all()

    if request.method == 'POST':
        gem_id = request.form['gem_id']
        middleman_id = request.form['middleman_id']
        date_borrowed = datetime.strptime(request.form['date_borrowed'], '%Y-%m-%d')
        
        gem = Gem.query.get_or_404(gem_id)
        gem.borrowed = True
        new_borrowed_gem = BorrowedGem(gem_id=gem_id, middleman_id=middleman_id, date_borrowed=date_borrowed)
        db.session.add(new_borrowed_gem)
        db.session.commit()
        flash('Borrowed gem recorded successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('borrow_gem.html', gems=gems, middlemen=middlemen)

@app.route('/delete_borrow_gem/<int:id>', methods=['GET'])
@login_required
def delete_borrow_gem(id):
    borrow_gem = BorrowedGem.query.get_or_404(id)
    db.session.delete(borrow_gem)
    db.session.commit()
    flash('Borrowed Gem record deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/return_or_sell/<int:id>', methods=['GET', 'POST'])
def return_or_sell(id):
    borrowed_gem = BorrowedGem.query.get_or_404(id)
    gem = Gem.query.get_or_404(borrowed_gem.gem_id)
    
    if request.method == 'POST':
        action = request.form['action']
        date_returned_or_sold = datetime.strptime(request.form['date_returned_or_sold'], '%Y-%m-%d')
        
        if action == 'return':
            gem.borrowed = False
            borrowed_gem.status = 'returned'
            borrowed_gem.date_returned_or_sold = date_returned_or_sold
            flash('Gem marked as returned!')
            
        elif action == 'sell':
            gem.sold = True
            gem.borrowed = False
            sold_price = float(request.form['sold_price'])
            bought_price = gem.price
            new_transaction = Transaction(gem_id=borrowed_gem.gem_id, date_sold=date_returned_or_sold, sold_price=sold_price, bought_price=bought_price)
            db.session.add(new_transaction)
            
            borrowed_gem.status = 'sold'
            borrowed_gem.date_returned_or_sold = date_returned_or_sold
            flash('Gem marked as sold!')
        
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('return_or_sell.html', borrowed_gem=borrowed_gem)

@app.route('/delete_transaction/<int:id>', methods=['GET'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/sell_gem/<id>', methods=['GET', 'POST'])
def sell_gem(id):
    gem = Gem.query.get_or_404(id)
    if request.method == 'POST':
        selling_price = request.form['selling_price']
        date_sold = datetime.strptime(request.form['date_sold'], '%Y-%m-%d')
        gem.sold = True
        bought_price = gem.price

        transaction = Transaction(
            gem_id=gem.id,
            date_sold=date_sold,
            sold_price=selling_price,
            bought_price=bought_price
        )

        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('sell_gem.html', gem=gem)

@app.route('/add_middleman', methods=['GET', 'POST'])
def add_middleman():
    if request.method == 'POST':
        name = request.form['name']
        contact_info = request.form['contact_info']
        
        new_middleman = Middleman(name=name, contact_info=contact_info)
        db.session.add(new_middleman)
        db.session.commit()
        flash('Middleman added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_middleman.html')

@app.route('/middlemen')
@login_required
def middlemen():
    middlemen = Middleman.query.all()
    return render_template('middlemen.html', middlemen=middlemen)

@app.route('/delete_middleman/<int:id>', methods=['GET'])
def delete_middleman(id):
    middleman = Middleman.query.get_or_404(id)
    db.session.delete(middleman)
    db.session.commit()
    flash('Middleman deleted successfully!')
    return redirect(url_for('middlemen'))

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/generate_report/<report_type>', methods=['GET', 'POST'])
@login_required
def generate_report(report_type):
    report_data = None
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            if end_date_obj < start_date_obj:
                flash("End date cannot be earlier than start date", "error")
            else:
                if report_type == 'sales':
                    report_data = generate_sales_report(start_date, end_date)
                    template = 'sales_report.html'
                elif report_type == 'inventory':
                    report_data = generate_inventory_report(start_date, end_date)
                    template = 'inventory_report.html'
                else:
                    flash('Invalid report type.', 'danger')
                    return redirect(url_for('generate_report', report_type=report_type))

                # Render the HTML template for display
                report_html = render_template(template, report_data=report_data)

               
                pdf_filename = f'{report_type}_{start_date}_{end_date}_report.pdf'
                # Return the rendered HTML to be displayed and provide download URL
                return render_template('report_display.html', report_html=report_html, download_url=url_for('download_report', filename=pdf_filename))

    return render_template('generate_report.html', report_type=report_type)

@app.route('/download_report/<filename>')
@login_required
def download_report(filename):
    try:
        # Generate the PDF again for download
        start_date, end_date = filename.split('_')[1], filename.split('_')[2]
        report_type = filename.split('_')[0]
        if report_type == 'sales':
            report_data = generate_sales_report(start_date, end_date)
            template = 'sales_report.html'
        elif report_type == 'inventory':
            report_data = generate_inventory_report(start_date, end_date)
            template = 'inventory_report.html'
        else:
            flash('Invalid report type.', 'danger')
            return redirect(url_for('generate_report', report_type=report_type))

        pdf_html = render_template(template, report_data=report_data)
        pdf = pdfkit.from_string(pdf_html, False, options={'page-size': 'A4', 'margin-top': '1cm', 'margin-right': '1cm', 'margin-bottom': '1cm', 'margin-left': '1cm'})
        pdf_io = io.BytesIO(pdf)

        # Send the PDF as an attachment without saving it locally
        return send_file(pdf_io, as_attachment=True, download_name=filename, mimetype='application/pdf')
    except FileNotFoundError:
        abort(404)
    except OSError as e:
        print(f"Error downloading {filename}: {e}")
        abort(500)

def generate_sales_report(start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    query = db.session.query(Transaction, Gem).join(Gem, Transaction.gem_id == Gem.id)
    if start_date == end_date:
        query = query.filter(db.func.date(Transaction.date_sold) == start_date)
    else:
        # Query the transactions within the specified date range
        query = query.filter(Transaction.date_sold.between(start_date, end_date))

    transactions = query.all()
    total_sales = sum(t.Transaction.sold_price for t in transactions)
    total_profit = sum(t.Transaction.sold_price - t.Transaction.bought_price for t in transactions)

    report_data = []
    for transaction, gem in transactions:
        report_data.append({
            'gem_id': gem.id,
            'gem_name': gem.name,
            'gem_type': gem.type,
            'quantity': gem.quantity,
            'weight': gem.weight,
            'bought_price': transaction.bought_price,
            'sold_price': transaction.sold_price,
            'sold_date': transaction.date_sold,
            'profit_made': transaction.sold_price - transaction.bought_price
        })

    return {
        'report_data': report_data,
        'total_sales': total_sales,
        'total_profit': total_profit
    }

def generate_inventory_report(start_date, end_date):
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    query = Gem.query.filter_by(sold=False)
    if start_date == end_date:
        query = query.filter(db.func.date(Gem.added_date) == start_date)
    else:
        query = query.filter(Gem.added_date.between(start_date, end_date))

    gems = query.all()
    total_value = sum(g.price for g in gems)

    report_data = []
    for gem in gems:
        report_data.append({
            'gem_id': gem.id,
            'gem_name': gem.name,
            'gem_type': gem.type,
            'bought_date': gem.added_date,
            'bought_price': gem.price
        })

    return {
        'report_data': report_data,
        'total_value': total_value
    }


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()