# app.py
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('index.html')

@app.route('/lp')
def lp():
    return render_template('lp.html')

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form['username']
    email = request.form['email']
    return f'ユーザー名: {username}, Eメール: {email}'

if __name__ == '__main__':
    app.run(debug=True)
