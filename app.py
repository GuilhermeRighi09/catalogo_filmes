import os
import uuid
import re
from functools import wraps

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave_mestra_123")


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)

    return decorated_function


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email_form = request.form["email"]
        password_form = request.form["password"]

        try:
            conn = get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)


            sql = "SELECT * FROM usuario WHERE email = %s"
            cursor.execute(sql, [email_form])
            usuario = cursor.fetchone()
            conn.close()


            if not usuario:
                return render_template("login.html", erro="Usuário não cadastrado")


            if check_password_hash(usuario['senha'], password_form):
                session['username'] = usuario['email']
                session['nome_usuario'] = usuario['nome']
                return redirect(url_for("listar_filmes"))
            else:

                return render_template("login.html", erro="Senha incorreta")

        except Exception as ex:
            return render_template("login.html", erro="Erro ao conectar ao banco")

    return render_template("login.html", erro=None)


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]


        if len(senha) < 8:
            return render_template("cadastro.html", erro="A senha deve ter no mínimo 8 caracteres")


        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
            return render_template("cadastro.html", erro="A senha deve conter pelo menos um caractere especial")


        senha_criptografada = generate_password_hash(senha)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            sql = "INSERT INTO usuario (nome, email, senha) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nome, email, senha_criptografada))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except Exception as ex:
            return render_template("cadastro.html", erro="E-mail já cadastrado ou erro no servidor")

    return render_template("cadastro.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route('/filmes', methods=['GET'])
@login_required
def listar_filmes():
    sql = "SELECT * FROM filmes ORDER BY id DESC"
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        filmes = cursor.fetchall()
        conn.close()
        return render_template("index.html", filmes=filmes)
    except Exception as ex:
        return jsonify({"message": "erro ao listar filmes"}), 500


@app.route("/novo", methods=["GET", "POST"])
@login_required
def novo_filme():
    if request.method == "POST":
        try:
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]
            file = request.files.get('capa')

            if file and allowed_file(file.filename):
                extensao = file.filename.rsplit('.', 1)[1].lower()
                nome_hash = f"{uuid.uuid4().hex}.{extensao}"

                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                caminho_abs = os.path.join(app.config['UPLOAD_FOLDER'], nome_hash)
                file.save(caminho_abs)
                url_capa = f"uploads/{nome_hash}"

                sql = "INSERT INTO filmes (titulo, genero, ano, url_capa) VALUES (%s, %s, %s, %s)"
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(sql, [titulo, genero, ano, url_capa])
                conn.commit()
                conn.close()
                return redirect(url_for("listar_filmes"))
            else:
                return "Arquivo inválido", 400
        except Exception as ex:
            return jsonify({"message": "erro ao cadastrar"}), 500
    return render_template("novo_filme.html")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_filme(id):
    try:
        conn = get_connection()
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]
            file = request.files.get('capa')
            url_capa = request.form.get("url_capa_atual")

            if file and allowed_file(file.filename):
                extensao = file.filename.rsplit('.', 1)[1].lower()
                nome_hash = f"{uuid.uuid4().hex}.{extensao}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_hash))
                url_capa = f"uploads/{nome_hash}"

            sql_update = "UPDATE filmes SET titulo = %s, genero = %s, ano = %s, url_capa = %s WHERE id = %s"
            cursor = conn.cursor()
            cursor.execute(sql_update, [titulo, genero, ano, url_capa, id])
            conn.commit()
            conn.close()
            return redirect(url_for("listar_filmes"))

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM filmes WHERE id = %s", [id])
        filme = cursor.fetchone()
        conn.close()
        return render_template("editar_filme.html", filme=filme)
    except Exception as ex:
        return jsonify({"message": "erro ao editar"}), 500


@app.route("/deletar/<int:id>", methods=["POST"])
@login_required
def deletar_filme(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM filmes WHERE id = %s", [id])
        conn.commit()
        conn.close()
        return redirect(url_for("listar_filmes"))
    except Exception as ex:
        return jsonify({"message": "erro ao deletar"}), 500


if __name__ == '__main__':
    app.run(debug=True)