from flask import Flask, render_template

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")


# ELASSAL_AUTH_V1: account routes are isolated in auth_routes.py
from auth_routes import auth_bp, configure_auth
configure_auth(app)
app.register_blueprint(auth_bp)

from network_lab import network_lab_bp
app.register_blueprint(network_lab_bp)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
