from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import requests, os

app = Flask(__name__)
# basedir = os.path.abspath(os.path.dirname(__file__))

app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/inventory_barang_mentah'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ma = Marshmallow(app)

results = {}

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(100))
    nama = db.Column(db.String(100))
    deskripsi = db.Column(db.String(200))
    jumlah = db.Column(db.Integer)

    def __init__(self, kode, nama, deskripsi, jumlah):
        self.kode = kode
        self.nama = nama
        self.deskripsi = deskripsi
        self.jumlah = jumlah

class ProductSchema(ma.Schema):
    class Meta:
        fields = ('id', 'kode', 'nama', 'deskripsi', 'jumlah')

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(100))
    nama = db.Column(db.String(100))
    deskripsi = db.Column(db.String(200))
    jumlah = db.Column(db.Integer)
    status = db.Column(db.Boolean, nullable=True)

    def __init__(self, kode, nama, deskripsi, jumlah, status):
        self.kode = kode
        self.nama = nama
        self.deskripsi = deskripsi
        self.jumlah = jumlah
        self.status = status

class RequestSchema(ma.Schema):
    class Meta:
        fields = ('id', 'kode', 'nama', 'deskripsi', 'jumlah', 'status')

request_schema = RequestSchema()
requests_schema = RequestSchema(many=True)



@app.route('/barang-mentah/tambah', methods=['POST'])
def tambah_barang():
    response = 500

    kode = request.form['kode']
    nama = request.form['nama']
    deskripsi = request.form['deskripsi']
    jumlah = request.form['jumlah']

    new_product = Product(kode, nama, deskripsi, jumlah)

    db.session.add(new_product)
    db.session.commit()

    results['message'] = 'Data Berhasil Dimasukkan'
    response = 200

    return results, response

@app.route('/barang-mentah', methods=['GET'])
def get_barang():

    results = {}
    response = 500

    all_product = Product.query.all()
    result = products_schema.dump(all_product)

    if not result:
        results['message'] = 'Data kosong'
        response = 400
    else:
        results['data'] = result
        response = 200

    return results, response
    
@app.route('/barang-mentah/select-one', methods=['GET'])
def get_a_barang():
    results = {}
    response = 500

    kode = request.form['kode']

    product = Product.query.filter_by(kode=kode)
    result = products_schema.dump(product)

    if not result:
        results['message'] = 'Data Tidak Ditemukan'
        response = 400
    else:
        results['data'] = result
        response = 200

    return results, response

@app.route('/barang-mentah/update-stock', methods=['PUT'])
def update_barang():

    results = {}
    response = 500

    kode = request.form['kode']
    jumlah = request.form['jumlah']

    product = Product.query.filter_by(kode=kode)
    result = products_schema.dump(product)

    if not result:
        results['message'] = 'Data Tidak Ditemukan'
        response = 400
    else:
        get_product = Product.query.filter_by(kode=kode).first()
        get_product.jumlah = jumlah
        db.session.commit()

        results['message'] = 'Berhasil Update Stock'
        response = 200

    return results, response

@app.route('/barang-mentah/delete', methods=['DELETE'])
def delete_barang():

    results = {}
    response = 500

    kode = request.form['kode']

    product = Product.query.filter_by(kode=kode)
    result = products_schema.dump(product)

    if not result:
        results['message'] = 'Data Tidak Ditemukan'
        response = 400
    else:
        get_product = Product.query.filter_by(kode=kode).first()
        db.session.delete(get_product)
        db.session.commit()

        results['message'] = 'Barang Berhasil Dihapus'
        response = 200

    return results, response

@app.route('/barang-mentah/store-produksi', methods=['POST'])
def request_produksi():
    response = 500

    kode = request.form['kode']
    nama = request.form['nama']
    deskripsi = request.form['deskripsi']
    jumlah = request.form['jumlah']
    status = 0

    new_request = Request(kode, nama, deskripsi, jumlah, status)

    db.session.add(new_request)
    db.session.commit()

    results['message'] = 'Permintaan diterima'
    response = 200

    return results, response

@app.route('/barang-mentah/kirim-produksi', methods=['POST'])
def send():
    results = {}
    response = 500

    url = 'http://192.168.1.114:8080/produksi/store-mentah'

    all_request = Request.query.filter_by(status=0)
    result = requests_schema.dump(all_request)

    if not result:
        results['message'] = 'Tidak Ada Permintaan'
        response = 400
    else:
        for item in result:
            data_id = item['id']
            nama_barang = item['nama']
            kode_barang = item['kode']
            keterangan = item['deskripsi']
            jumlah = item['jumlah']

        data = {
            'nama_barang': nama_barang,
            'kode_barang': kode_barang,
            'keterangan': keterangan,
            'jumlah': jumlah
        }

        requests.post(url, data = data)

        sent = Request.query.get(data_id)

        status = 1

        sent.status = status

        db.session.commit()

        results['message'] = 'Data dikirim'
        response = 200

    return results, response

@app.route('/barang-mentah/store-purchasing', methods=['POST'])
def store_purchasing():
    results = {}
    response = 500

    kode = request.form['kode']
    nama = request.form['nama']
    deskripsi = request.form['deskripsi']
    jumlah = request.form['jumlah']

    product = Product.query.filter_by(kode=kode)
    result = products_schema.dump(product)

    if not result:
        results['message'] = 'Data Tidak Ditemukan'
        response = 400
    else:
        get_product = Product.query.filter_by(kode=kode).first()

        product.jumlah = jumlah

        db.session.commit()

        results['message'] = 'Barang Diterima'
        response = 200

    return results, response

@app.route('/barang-mentah/request-purchasing', methods=['GET'])
def sent():
    results = {}
    response = 500
    list_request = []

    all_product = Product.query.filter_by(jumlah=0)
    result = products_schema.dump(all_product)

    if not result:
        results['message'] = 'Tidak Ada Permintaan'
        response = 400
    else:
        for item in result:
            list_request.append(item)

        results['message'] = 'Data Ditemukan'
        results['data'] = list_request
        response = 200

    return results, response


if __name__ == '__main__':
    app.run(host='0.0.0.0')