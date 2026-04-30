import os
import uuid
from flask import Flask, request, jsonify, render_template, redirect, url_for
from psycopg2.extras import RealDictCursor
from database import get_connection

app = Flask(__name__)

# Configurações para Upload
UPLOAD_FOLDER = 'static/uploads'
# REQUISITO: Permite apenas jpeg, jpg, png
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return redirect(url_for('listar_filmes'))


@app.route('/filmes', methods=['GET'])
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
def novo_filme():
    if request.method == "POST":
        try:
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            # 1. Receba o arquivo através da requisição
            file = request.files.get('capa')

            # REQUISITO: Validação rigorosa de extensão
            if file and allowed_file(file.filename):
                # 2. Renomeie o arquivo para uma hash única (UUID)
                extensao = file.filename.rsplit('.', 1)[1].lower()
                nome_hash = f"{uuid.uuid4().hex}.{extensao}"

                # Salva o arquivo na pasta static/uploads
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                caminho_abs = os.path.join(app.config['UPLOAD_FOLDER'], nome_hash)
                file.save(caminho_abs)

                # 3. Salve o caminho relativo no banco de dados
                url_capa = f"uploads/{nome_hash}"

                sql = "INSERT INTO filmes (titulo, genero, ano, url_capa) VALUES (%s, %s, %s, %s)"
                params = [titulo, genero, ano, url_capa]

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                conn.close()
                return redirect(url_for("listar_filmes"))
            else:
                return "Erro: Extensão de arquivo não permitida (Use apenas JPG, JPEG ou PNG)", 400

        except Exception as ex:
            print('Erro:', str(ex))
            return jsonify({"message": "erro ao cadastrar filme"}), 500

    return render_template("novo_filme.html")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_filme(id):
    try:
        conn = get_connection()
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            # Lógica para manter a imagem atual ou subir uma nova
            file = request.files.get('capa')
            url_capa = request.form.get("url_capa_atual")  # Campo hidden no HTML

            if file and allowed_file(file.filename):
                extensao = file.filename.rsplit('.', 1)[1].lower()
                nome_hash = f"{uuid.uuid4().hex}.{extensao}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_hash))
                url_capa = f"uploads/{nome_hash}"

            sql_update = "UPDATE filmes SET titulo = %s, genero = %s, ano = %s, url_capa = %s WHERE id = %s"
            params = [titulo, genero, ano, url_capa, id]

            cursor = conn.cursor()
            cursor.execute(sql_update, params)
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