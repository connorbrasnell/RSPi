from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
from werkzeug.contrib.fixers import ProxyFix
import os
import hashlib

app = Flask(__name__)
app.secret_key = os.urandom(12)

loggedIn = False

@app.route('/')
def home():
    
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('loggedin.html')

@app.route('/login', methods=['POST'])
def do_admin_login():

    password = request.form['password']

    hashFile = open("data_files/webInterface.txt","r").read()
    splitData = hashFile.split('\n')

    pwdHash = splitData[0]
    pwdSalt = splitData[1]
    uname = splitData[2]

    password = password + pwdSalt
    password = password.encode('utf-8')
    
    usrPwdHash = hashlib.sha512(password).hexdigest()

    if usrPwdHash == pwdHash and request.form['username'] == uname:
        session['logged_in'] = True
    else:
        flash('Wrong Username or Password!')
    return home()

@app.route("/sendText", methods=['POST'])
def change_text():
    
    output = open('data_files/managerCorner.txt', 'w').close()
    output = open('data_files/managerCorner.txt', 'w')
    output.write(request.form['managerCornerText'])
    output.close()

    return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    #app.run(ssl_context=('certs/cert.pem','certs/key.pem'))
    app.run()
