from flask import Flask, jsonify, request, redirect, url_for, render_template, flash, session
import sqlite3 as sql
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "admin123"

@app.route("/")
@app.route("/index")
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('search_query', '')
    con = sql.connect("form_db.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    
    if search_query:
        cur.execute("SELECT * FROM users WHERE NOME LIKE ?", ('%' + search_query + '%',))
    else:
        cur.execute("SELECT * FROM users")
    
    data = cur.fetchall()
    return render_template("index.html", datas=data, username=session['username'])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        con = sql.connect("form_db.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM admin WHERE username=?", (username,))
        user = cur.fetchone()

        if user and user[2] == password:  # Comparação direta da senha
            session['username'] = user[1]  # Armazena o nome de usuário na sessão
            flash("Logado com sucesso", "success")
            return redirect(url_for('index'))
        else:
            flash("Senha ou login inválido", "danger")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("Deslogado com sucesso", "success")
    return redirect(url_for('login'))

@app.route("/user_details/<int:id>")
def view_user(id):
    con = sql.connect("form_db.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE ID=?", (id,))
    data = cur.fetchone()
    
    if data:
        user = {
            "NOME": data["NOME"],
            "IDADE": data["IDADE"],
            "ENDERECO": data["ENDERECO"],
            "LOGRADOURO": data["LOGRADOURO"],
            "CIDADE": data["CIDADE"],
            "ESTADO": data["ESTADO"],
            "EMAIL": data["EMAIL"]
        }
        return jsonify(user)
    else:
        return jsonify({"error": "Usuário não encontrado"}), 404

@app.route("/add_user", methods=["POST", "GET"])
def add_user():
    if request.method == "POST":
        nome = request.form["nome"]
        idade = request.form["idade"]
        endereco = request.form["endereco"]
        logradouro = request.form["logradouro"]
        cidade = request.form["cidade"]
        estado = request.form["estado"]
        email = request.form["email"]
        
        con = sql.connect('form_db.db')
        cur = con.cursor()
        cur.execute("INSERT INTO users (NOME, IDADE, ENDERECO, LOGRADOURO, CIDADE, ESTADO, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (nome, idade, endereco, logradouro, cidade, estado, email))
        con.commit()
        flash("Dados cadastrados", "success")
        return redirect(url_for("index"))
    return render_template("add_user.html")

@app.route("/edit_user/<string:id>", methods=["POST", "GET"])
def edit_user(id):
    if request.method == "POST":
        nome = request.form["nome"]
        idade = request.form["idade"]
        endereco = request.form["endereco"]
        logradouro = request.form["logradouro"]
        cidade = request.form["cidade"]
        estado = request.form["estado"]
        email = request.form["email"]
        
        with sql.connect('form_db.db') as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE users 
                SET NOME=?, IDADE=?, ENDERECO=?, LOGRADOURO=?, CIDADE=?, ESTADO=?, EMAIL=? 
                WHERE ID=?
            """, (nome, idade, endereco, logradouro, cidade, estado, email, id))
            con.commit()
            flash("Dados atualizados com sucesso", "success")
        return redirect(url_for("index"))
    
    con = sql.connect("form_db.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE ID=?", (id,))
    data = cur.fetchone()
    return render_template("edit_user.html", datas=data)

@app.route("/delete_user/<string:id>", methods=["GET"])
def delete_user(id):
    con = sql.connect('form_db.db')
    cur = con.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (id,))
    con.commit()
    flash("Dados Deletados", "warning")
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(debug=True)