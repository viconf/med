from flask import Flask, jsonify, render_template_string, request, redirect, send_file, url_for, render_template, flash, session, send_from_directory
import sqlite3 as sql
import subprocess
import os
from fpdf import FPDF
from datetime import date, datetime
from openpyxl import Workbook, load_workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd


app = Flask(__name__)
app.secret_key = "admin123"

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
            session['username'] = user[1]
            session['nome_medico'] = user[3]  # Nome do médico
            session['especialidade'] = user[4]  # Especialidade
            session['crm'] = user[5]  # CRM
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
            "EMAIL": data["EMAIL"],
            "SEXO": data["SEXO"],
            "NASCIMENTO": data["NASCIMENTO"],
            "ESCOLARIDADE": data["ESCOLARIDADE"],
            "TELEFONE": data["TELEFONE"],
            "CPF": data["CPF"],
            "RG": data["RG"]
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
        sexo = request.form["sexo"]
        nascimento = request.form["nascimento"]
        escolaridade = request.form["escolaridade"]
        telefone = request.form["telefone"]
        cpf = request.form["cpf"]
        rg = request.form["rg"]
        
        # Convertendo a data de nascimento para o formato desejado
        nascimento_formatado = datetime.strptime(nascimento, "%Y-%m-%d").strftime("%d/%m/%Y")

        con = sql.connect('form_db.db')
        cur = con.cursor()
        cur.execute("INSERT INTO users (NOME, IDADE, ENDERECO, LOGRADOURO, CIDADE, ESTADO, EMAIL, SEXO, NASCIMENTO, ESCOLARIDADE, TELEFONE, CPF, RG) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (nome, idade, endereco, logradouro, cidade, estado, email, sexo, nascimento_formatado, escolaridade, telefone, cpf, rg))
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
        sexo = request.form["sexo"]
        nascimento = request.form["nascimento"]
        escolaridade = request.form["escolaridade"]
        telefone = request.form["telefone"]
        cpf = request.form["cpf"]
        rg = request.form["rg"]
        
        # Convertendo a data de nascimento para o formato desejado
        nascimento_formatado = datetime.strptime(nascimento, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        with sql.connect('form_db.db') as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE users 
                SET NOME=?, IDADE=?, ENDERECO=?, LOGRADOURO=?, CIDADE=?, ESTADO=?, EMAIL=?, SEXO=?, NASCIMENTO=?, ESCOLARIDADE=?, TELEFONE=?, CPF=?, RG=?
                WHERE ID=?
            """, (nome, idade, endereco, logradouro, cidade, estado, email, sexo, nascimento_formatado, escolaridade, telefone, cpf, rg, id))
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

@app.route("/generate_ficha/<int:id>", methods=["GET"])
def generate_ficha(id):
    con = sql.connect("form_db.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE ID=?", (id,))
    cliente = cur.fetchone() 
    if cliente:
        user = {
            "NOME": cliente["NOME"],
            "IDADE": cliente["IDADE"],
            "ENDERECO": cliente["ENDERECO"],
            "LOGRADOURO": cliente["LOGRADOURO"],
            "CIDADE": cliente["CIDADE"],
            "ESTADO": cliente["ESTADO"],
            "EMAIL": cliente["EMAIL"],
            "SEXO": cliente["SEXO"],
            "NASCIMENTO": cliente["NASCIMENTO"],
            "ESCOLARIDADE": cliente["ESCOLARIDADE"],
            "TELEFONE": cliente["TELEFONE"],
            "CPF": cliente["CPF"],
            "RG": cliente["RG"]
        }
        return render_template('add_attendance.html', cliente=user)
        
    else:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
@app.route("/add_attendance", methods=["POST", "GET"])
def add_attendance():
    if request.method == "POST":
        # Gerando o prontuário automático
        con = sql.connect('form_db.db')
        cur = con.cursor()
        cur.execute("INSERT INTO prontuario DEFAULT VALUES")
        con.commit()
        
        cur.execute("SELECT last_insert_rowid()")
        prontuario = cur.fetchone()[0]
        
        registro = request.form["registro"]
        data_atendimento = request.form["data_atendimento"]
        data_alta = request.form["data_alta"]
        paciente_nome = request.form["paciente_nome"]
        paciente_sexo = request.form["paciente_sexo"]
        paciente_data_nascimento = request.form["paciente_data_nascimento"]
        paciente_idade = request.form["paciente_idade"]
        paciente_raca = request.form["paciente_raca"]
        paciente_telefone = request.form["paciente_telefone"]
        paciente_rg = request.form["paciente_rg"]
        paciente_cpf = request.form["paciente_cpf"]
        paciente_convenio = request.form["paciente_convenio"]
        recepcao = request.form["recepcao"]
        caracter = request.form["caracter"]
        pressao = request.form["pressao"]
        temperatura = request.form["temperatura"]
        peso = request.form["peso"]
        saturacao_o2 = request.form["saturacao_o2"]
        dextro = request.form["dextro"]
        frequencia_cardiaca = request.form["frequencia_cardiaca"]
        frequencia_respiratoria = request.form["frequencia_respiratoria"]
        situacao_queixa = request.form["situacao_queixa"]
        alergia = request.form["alergia"]
        uso_medicacao = request.form["uso_medicacao"]
        historico_saude = request.form["historico_saude"]
        classificacao_risco = request.form["classificacao_risco"]
        anamnese = request.form["anamnese"]
        exames_fisicos = request.form["exames_fisicos"]
        conduta = request.form["conduta"]
        prescricao_medica = request.form["prescricao_medica"]
        cid = request.form["cid"]
        # Inserindo dados no banco de dados
        cur.execute("""
            INSERT INTO attendances (PRONTUARIO, REGISTRO, DATA_ATENDIMENTO, DATA_ALTA, PACIENTE_NOME, PACIENTE_SEXO, PACIENTE_DATA_NASCIMENTO, PACIENTE_IDADE, PACIENTE_RACA, PACIENTE_TELEFONE, PACIENTE_RG, PACIENTE_CPF, PACIENTE_CONVENIO, RECEPCAO, CARACTER, PRESSAO, TEMPERATURA, PESO, SATO2, DEXTRO, FREQUENCIA_CARDIACA, FREQUENCIA_RESPIRATORIA, SITUACAO_QUEIXA, ALERGIA, USO_MEDICACAO, HISTORICO_SAUDE, CLASSIFICACAO_RISCO, ANAMNESE, EXAMES_FISICOS, CONDUTA, PRESCRICAO_MEDICA, CID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (prontuario, registro, data_atendimento, data_alta, paciente_nome, paciente_sexo, paciente_data_nascimento, paciente_idade, paciente_raca, paciente_telefone, paciente_rg, paciente_cpf, paciente_convenio, recepcao, caracter, pressao, temperatura, peso, saturacao_o2, dextro, frequencia_cardiaca, frequencia_respiratoria, situacao_queixa, alergia, uso_medicacao, historico_saude, classificacao_risco, anamnese, exames_fisicos, conduta, prescricao_medica, cid))
        
        con.commit()
        flash("Atendimento cadastrado com sucesso", "success")
        pdf_path = generate_and_convert_excel({
            'prontuario': prontuario,
            'registro': registro,
            'data_atendimento': data_atendimento,
            'data_alta': data_alta,
            'paciente_nome': paciente_nome,
            'paciente_sexo': paciente_sexo,
            'paciente_data_nascimento': paciente_data_nascimento,
            'paciente_idade': paciente_idade,
            'paciente_raca': paciente_raca,
            'paciente_telefone': paciente_telefone,
            'paciente_rg': paciente_rg,
            'paciente_cpf': paciente_cpf,
            'paciente_convenio': paciente_convenio,
            'recepcao': recepcao,
            'caracter': caracter,
            'pressao': pressao,
            'temperatura': temperatura,
            'peso': peso,
            'saturacao_o2': saturacao_o2,
            'dextro': dextro,
            'frequencia_cardiaca': frequencia_cardiaca,
            'frequencia_respiratoria': frequencia_respiratoria,
            'situacao_queixa': situacao_queixa,
            'alergia': alergia,
            'uso_medicacao': uso_medicacao,
            'historico_saude': historico_saude,
            'classificacao_risco': classificacao_risco,
            'anamnese': anamnese,
            'exames_fisicos': exames_fisicos,
            'conduta': conduta,
            'prescricao_medica': prescricao_medica,
            'cid': cid
        })
        cur.execute("UPDATE attendances SET pdf=? WHERE prontuario=?", (pdf_path, prontuario))
        con.commit()

        if pdf_path:
            flash(f"Arquivo Excel gerado em: {pdf_path}", "info")
        else:
            flash("Erro ao gerar o arquivo Excel", "error")
            
        return redirect(url_for("index"))
    
    return render_template("add_attendance.html")
    
def generate_and_convert_excel(data):
    template_path = 'modelo.xlsx'
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"prontuario_{data['prontuario']}.xlsx")
    
    # Carregar o template
    workbook = load_workbook(template_path)
    sheet = workbook.active
    
    # Preencher o template com os dados
    sheet['D22'] = data['prontuario']
    sheet['I22'] = data['registro']
    sheet['Q22'] = data['data_atendimento']
    sheet['V22'] = data['data_alta']
    sheet['C25'] = data['paciente_nome']
    sheet['B27'] = data['paciente_sexo']
    sheet['H27'] = data['paciente_data_nascimento']
    sheet['N27'] = data['paciente_idade']
    sheet['S27'] = data['paciente_raca']
    sheet['U29'] = data['paciente_telefone']
    sheet['I29'] = data['paciente_rg']
    sheet['O29'] = data['paciente_cpf']
    sheet['W27'] = data['paciente_convenio']
    sheet['C29'] = data['recepcao']
    sheet['K34'] = data['caracter']
    sheet['F39'] = data['pressao']
    sheet['L39'] = data['temperatura']
    sheet['R39'] = data['peso']
    sheet['V39'] = data['saturacao_o2']
    sheet['C41'] = data['dextro']
    sheet['O41'] = data['frequencia_cardiaca']
    sheet['V41'] = data['frequencia_respiratoria']
    sheet['E43'] = data['situacao_queixa']
    sheet['C46'] = data['alergia']
    sheet['F48'] = data['uso_medicacao']
    sheet['F50'] = data['historico_saude']
    sheet['G52'] = data['classificacao_risco']
    sheet['A62'] = data['anamnese']
    sheet['A66'] = data['exames_fisicos']
    sheet['A87'] = data['conduta']
    sheet['A92'] = data['prescricao_medica']
    sheet['A102'] = data['cid']
    sheet['h54'] = f"Dr. {session['nome_medico']}"
    sheet['u119'] = f" {session['nome_medico']}"
    sheet['t120'] = f" {session['crm']}"
    workbook.save(output_path)
    return output_path
@app.route('/attendance_chart/<int:user_id>',methods=["GET"])
def attendance_chart(user_id):
    conn = sql.connect('form_db.db')
    conn.row_factory = sql.Row  # Define o retorno como dicionário-like
    cursor = conn.cursor()

    # Consulta SQL para contar os atendimentos por mês
    cursor.execute("""
        SELECT strftime('%m', a.DATA_ATENDIMENTO) AS mes, count(*) AS total_atendimentos
        FROM attendances a
        INNER JOIN users u ON u.NOME = a.PACIENTE_NOME AND u.CPF = a.PACIENTE_CPF
        WHERE u.ID = ?
        GROUP BY mes
        ORDER BY mes
    """, (user_id,))
    
    rows = cursor.fetchall()
    months = []
    counts = []
    
    # Formatar os dados para enviar como JSON
    for row in rows:
        months.append(row['mes'])  # Acessa pelo nome da coluna
        counts.append(row['total_atendimentos'])  # Acessa pelo nome da coluna

    conn.close()
    print(months, counts)  # Debug para verificar os dados antes de retornar
    
    return jsonify({'months': months, 'counts': counts})

if __name__ == "__main__":
    
    app.run(debug=True)
