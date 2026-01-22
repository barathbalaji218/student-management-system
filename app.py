from flask import Flask, render_template
from app import create_app

app= create_app()

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)