from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_aman')
# Koneksi ke database SQLite
def get_db_connection():
    conn = sqlite3.connect('dbSqlite.db')  # pastikan nama file database sesuai
    conn.row_factory = sqlite3.Row  # Memungkinkan hasil query seperti dictionary
    print("Database Connected Successfully!")
    return conn

# Halaman utama yang menampilkan daftar buku
@app.route('/')
def index():
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM Buku').fetchall()  # Menggunakan nama tabel 'Buku' (huruf kapital)
    conn.close()
    return render_template('index.html', books=books)

# Halaman untuk menambah buku
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        judul = request.form['judul']
        penulis = request.form['penulis']
        tahun = request.form['tahun']

        conn = get_db_connection()
        conn.execute('INSERT INTO Buku (judul, penulis, tahun) VALUES (?, ?, ?)',
                     (judul, penulis, tahun))  # Menggunakan nama tabel 'Buku'
        conn.commit()
        conn.close()

        return redirect('/')  # Setelah menambah, kembali ke halaman utama

    return render_template('add.html')

@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    # Koneksi ke database
    conn = get_db_connection()
    
    # Hapus buku berdasarkan ID
    conn.execute('DELETE FROM Buku WHERE id = ?', (id,))
    conn.execute("DELETE FROM sqlite_sequence WHERE name='Buku'")
    conn.execute("""
        UPDATE Buku
        SET id = rowid
    """)

    conn.commit()  # Menyimpan perubahan
    conn.close()  # Menutup koneksi

    # Setelah buku dihapus, arahkan kembali ke halaman utama
    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()
    
    # Ambil data buku berdasarkan ID
    book = conn.execute('SELECT * FROM Buku WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        # Ambil data baru dari form
        judul = request.form['judul']
        penulis = request.form['penulis']
        tahun = request.form['tahun']
        
        # Update data buku di database
        conn.execute('UPDATE Buku SET judul = ?, penulis = ?, tahun = ? WHERE id = ?',
                     (judul, penulis, tahun, id))
        conn.commit()  # Menyimpan perubahan
        conn.close()  # Menutup koneksi
        
        # Setelah data diupdate, arahkan ke halaman utama
        return redirect('/')
    
    # Jika request GET, tampilkan form dengan data buku
    conn.close()
    return render_template('edit.html', book=book)

@app.route('/peminjaman', methods=['GET', 'POST'])
def peminjaman():
    if request.method == 'POST':
        # Ambil data dari form
        id_buku = request.form['id_buku']
        nama_peminjam = request.form['nama_peminjam']
        tanggal_pinjam = request.form['tanggal_pinjam']
        tanggal_kembali = request.form['tanggal_kembali']
        status = request.form['status']

        # Simpan ke database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Peminjaman (id_buku, nama_peminjam, tanggal_pinjam, tanggal_kembali, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_buku, nama_peminjam, tanggal_pinjam, tanggal_kembali, status))
        conn.commit()
        conn.close()

        # Redirect ke GET agar tidak submit ulang jika reload halaman
        return redirect(url_for('peminjaman'))

    # Untuk GET: ambil data buku dan peminjaman
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
    conn = get_db_connection()
    conn.execute('DELETE FROM Peminjaman WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('peminjaman'))

@app.route('/edit_peminjaman/<int:id>', methods=['GET', 'POST'])
def edit_peminjaman(id):
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


if __name__ == "__main__":
    app.run(debug=True)
