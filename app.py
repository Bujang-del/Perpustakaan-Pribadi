from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import date
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_aman')

# Koneksi ke database SQLite
def get_db_connection():
    conn = sqlite3.connect('dbSqlite.db')
    conn.row_factory = sqlite3.Row
    print("Database Connected Successfully!")
    return conn

# ---------------- AUTHORITY ----------------


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Tentukan role berdasarkan email
        if email == 'sibabihutan5@gmail.com':
            role = 'admin'
        else:
            role = 'member'

        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (username, hashed_pw, role))
            conn.commit()
            flash(f'Akun berhasil dibuat sebagai {role.upper()}. Silakan login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username sudah digunakan.', 'danger')
        finally:
            conn.close()

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login berhasil.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout berhasil.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    if session['role'] == 'admin':
        return redirect(url_for('index'))
    else:
        return redirect(url_for('member'))

# ---------------- MEMBER VIEW ----------------

@app.route('/member')
def member():
    if session.get('role') != 'member':
        return "Akses hanya untuk member."

    query = request.args.get('q', '').strip()
    conn = get_db_connection()

    if query:
        books = conn.execute('''
            SELECT * FROM Buku 
            WHERE judul LIKE ? OR penulis LIKE ?
        ''', (f'%{query}%', f'%{query}%')).fetchall()
    else:
        books = conn.execute('SELECT * FROM Buku').fetchall()

    conn.close()
    return render_template('member.html', books=books, username=session.get('username'), query=query)




# ---------------- CRUD BUKU (ADMIN) ----------------

@app.route('/')
def index():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    books = conn.execute('SELECT * FROM Buku').fetchall()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if session.get('role') != 'admin':
        return "Akses hanya untuk admin."

    if request.method == 'POST':
        judul = request.form['judul']
        penulis = request.form['penulis']
        tahun = request.form['tahun']

        conn = get_db_connection()
        conn.execute('INSERT INTO Buku (judul, penulis, tahun) VALUES (?, ?, ?)',
                     (judul, penulis, tahun))
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('add.html')

@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    if session.get('role') != 'admin':
        return "Akses hanya untuk admin."

    conn = get_db_connection()
    conn.execute('DELETE FROM Buku WHERE id = ?', (id,))
    conn.execute("DELETE FROM sqlite_sequence WHERE name='Buku'")
    conn.execute("UPDATE Buku SET id = rowid")
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if session.get('role') != 'admin':
        return "Akses hanya untuk admin."

    conn = get_db_connection()
    book = conn.execute('SELECT * FROM Buku WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        judul = request.form['judul']
        penulis = request.form['penulis']
        tahun = request.form['tahun']
        conn.execute('UPDATE Buku SET judul = ?, penulis = ?, tahun = ? WHERE id = ?',
                     (judul, penulis, tahun, id))
        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('edit.html', book=book)

# ---------------- CRUD PEMINJAMAN (ADMIN) ----------------

@app.route('/peminjaman', methods=['GET', 'POST'])
def peminjaman():
    if session.get('role') != 'admin':
        return "Akses hanya untuk admin."

    if request.method == 'POST':
        id_buku = request.form['id_buku']
        nama_peminjam = request.form['nama_peminjam']
        tanggal_pinjam = request.form['tanggal_pinjam']
        tanggal_kembali = request.form['tanggal_kembali']
        status = request.form['status']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Peminjaman (id_buku, nama_peminjam, tanggal_pinjam, tanggal_kembali, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_buku, nama_peminjam, tanggal_pinjam, tanggal_kembali, status))
        conn.commit()
        conn.close()

        return redirect(url_for('peminjaman'))

    book_id = request.args.get('book_id', type=int)
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM Buku').fetchall()
    selected_book = None
    if book_id:
        selected_book = conn.execute('SELECT * FROM Buku WHERE id = ?', (book_id,)).fetchone()

    peminjaman = conn.execute('''
        SELECT Peminjaman.id, Buku.judul, Peminjaman.nama_peminjam, 
               Peminjaman.tanggal_pinjam, Peminjaman.tanggal_kembali, Peminjaman.status
        FROM Peminjaman
        JOIN Buku ON Peminjaman.id_buku = Buku.id
    ''').fetchall()

    current_date = date.today().isoformat()
    conn.close()

    return render_template('peminjaman.html', 
                           peminjaman=peminjaman, 
                           books=books, 
                           selected_book=selected_book,
                           current_date=current_date)

@app.route('/delete_peminjaman/<int:id>', methods=['POST', 'GET'])
def delete_peminjaman(id):
    if session.get('role') != 'admin':
        return "Akses hanya untuk admin."

    conn = get_db_connection()
    conn.execute('DELETE FROM Peminjaman WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('peminjaman'))

@app.route('/edit_peminjaman/<int:id>', methods=['GET', 'POST'])
def edit_peminjaman(id):
    if session.get('role') != 'admin':
        return "Akses hanya untuk admin."

    conn = get_db_connection()
    peminjaman = conn.execute('SELECT * FROM Peminjaman WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        nama_peminjam = request.form['nama_peminjam']
        tanggal_pinjam = request.form['tanggal_pinjam']
        tanggal_kembali = request.form['tanggal_kembali']
        status = request.form['status']

        conn.execute('''
            UPDATE Peminjaman
            SET nama_peminjam = ?, tanggal_pinjam = ?, tanggal_kembali = ?, status = ?
            WHERE id = ?
        ''', (nama_peminjam, tanggal_pinjam, tanggal_kembali, status, id))
        conn.commit()
        conn.close()
        return redirect(url_for('peminjaman'))

    conn.close()
    return render_template('edit_peminjaman.html', peminjaman=peminjaman)

# ---------------- MAIN ----------------

if __name__ == "__main__":
    app.run(debug=True)
