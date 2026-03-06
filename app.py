from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from textblob import TextBlob

app = Flask(__name__)
app.secret_key = "secretkey123"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# DATABASE MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(200))


class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    sentiment = db.Column(db.String(20))   # ADD THIS
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# =========================
# ROUTES
# =========================

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password"

    return render_template('login.html', error=error)


# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form['password'])
        new_user = User(
            full_name=request.form['full_name'],
            username=request.form['username'],
            email=request.form['email'],
            phone=request.form['phone'],
            password=hashed
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # 🔥 IMPORTANT FIX
    if not user:
        session.clear()
        return redirect(url_for('login'))

    entries = JournalEntry.query.filter_by(user_id=user.id).all()

    return render_template('dashboard.html', user=user, entries=entries)

# ================= NEW ENTRY =================
@app.route('/new_entry', methods=['POST'])
def new_entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    content = request.form['content']

    # Sentiment Analysis
    analysis = TextBlob(content)
    polarity = analysis.sentiment.polarity

    if polarity > 0:
        mood = "Positive 😊"
    elif polarity < 0:
        mood = "Negative 😔"
    else:
        mood = "Neutral 😐"

    # 🔥 CREATE entry properly
    entry = JournalEntry(
        title=title,
        content=content,
        sentiment=mood,
        user_id=session['user_id']
    )

    db.session.add(entry)
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/entry/<int:id>')
def view_entry(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    entry = JournalEntry.query.get_or_404(id)

    # Security check
    if entry.user_id != session['user_id']:
        return "Unauthorized"

    user = User.query.get(session['user_id'])
    entries = JournalEntry.query.filter_by(user_id=user.id).all()

    return render_template(
        'dashboard.html',
        user=user,
        entries=entries,
        selected_entry=entry
    )

# ================= SEARCH =================
@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = request.args.get('q')

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('login'))
    else:
        entries = JournalEntry.query.filter_by(
            user_id=session['user_id']
        ).all()

    return render_template(
        'dashboard.html',
        user=user,
        entries=entries,
        selected_entry=None
    )


@app.route('/delete/<int:id>')
def delete_entry(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    entry = JournalEntry.query.get_or_404(id)

    if entry.user_id != session['user_id']:
        return "Unauthorized"

    db.session.delete(entry)
    db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_entry(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    entry = JournalEntry.query.get_or_404(id)

    if request.method == 'POST':
        entry.title = request.form['title']
        entry.content = request.form['content']
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('edit.html', entry=entry)


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)