import os, uuid
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, Response
from functools import wraps
import db_news
import scraper

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# ─── SISTEM KEAMANAN ADMIN ───
def check_auth(username, password):
    # Username: admin | Password: a123
    return username == 'admin' and password == 'a123'

def authenticate():
    return Response(
    'Akses Ditolak. Anda harus login sebagai Admin.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ─── HALAMAN PUBLIK ───
@app.route('/')
def index():
    articles = db_news.get_all()
    popular = db_news.get_popular()
    return render_template('index.html', articles=articles, popular=popular)

@app.route('/kategori/<cat>')
def category(cat):
    articles = db_news.get_by_cat(cat)
    popular = db_news.get_popular()
    return render_template('category.html', articles=articles, category=cat, popular=popular)

@app.route('/baca/<int:aid>')
def read(aid):
    article = db_news.get_by_id(aid)
    if not article:
        return "Berita tidak ditemukan", 404
    popular = db_news.get_popular()
    return render_template('article.html', article=article, popular=popular)

# ─── AREA TERLARANG (HANYA ADMIN) ───
@app.route('/refresh')
@requires_auth
def refresh():
    scraper.NewsAggregator().run_all()
    return redirect(url_for('admin'))

@app.route('/admin')
@requires_auth
def admin():
    articles = db_news.get_all()
    return render_template('admin.html', articles=articles)

@app.route('/admin/tambah', methods=['GET', 'POST'])
@requires_auth
def add():
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        author = request.form['author']
        content = request.form['content']
        image_path = None
        file = request.files.get('image_file')
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex[:10]}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"uploads/{filename}"
        db_news.add_manual(title, category, author, content, image_path)
        return redirect(url_for('admin'))
    return render_template('add.html')

@app.route('/admin/hapus/<int:aid>')
@requires_auth
def delete(aid):
    db_news.delete(aid)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    db_news.init_db()
    app.run(host='127.0.0.1', port=8080, debug=True)
