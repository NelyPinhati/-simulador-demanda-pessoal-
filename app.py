# This is the project structure for a Python web application named "matching-ia"

matching-ia/
├── app.py             # Main application entry point (likely Flask or FastAPI)
├── matching.py        # Core matching logic or algorithms
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker container configuration
├── README.md          # Project documentation
├── templates/
│   └── index.html     # HTML template(s) for the web app
├── static/
│   └── style.css      # CSS styles for the web app
from flask import Flask, render_template, request
from matching import calcular_matching

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    if request.method == "POST":
        vaga = request.form.get("vaga")
        cv = request.form.get("cv")
        score, explicacoes = calcular_matching(cv, vaga)
        resultado = {"score": score, "explicacoes": explicacoes}
    return render_template("index.html", resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
    from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def calcular_matching(cv_texto, vaga_texto):
    cv_embedding = model.encode(cv_texto, convert_to_tensor=True)
    vaga_embedding = model.encode(vaga_texto, convert_to_tensor=True)
    
    score = util.cos_sim(cv_embedding, vaga_embedding).item() * 100

    explicacao = []
    if "Python" in cv_texto and "Python" in vaga_texto:
        explicacao.append("Possui habilidade em Python.")
    if "AWS" in cv_texto and "AWS" in vaga_texto:
        explicacao.append("Experiência com AWS detectada.")
    if "liderança" in cv_texto.lower():
        explicacao.append("Candidato demonstra perfil de liderança.")

    return round(score, 2), explicacao
