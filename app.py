#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, flash, jsonify, redirect, url_for, session, request, logging
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from sqlhelpers import *
from forms import * 
from functools import wraps
from final_model import define_model1
import tensorflow as tf
import pandas as pd 
import numpy as np 
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
from pathlib import Path
import string
import re
import joblib
import io
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify
from fer import FER 
import json
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pickle
from flask import Flask, render_template, flash, jsonify, redirect, url_for, session, request, logging
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from sqlhelpers import *
from forms import * 
from functools import wraps
from werkzeug.utils import secure_filename
import os
import random
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import plot_model
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Embedding, Dense, Flatten, Conv1D, MaxPooling1D, SimpleRNN, GRU, LSTM, Input, Dropout, Bidirectional
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import LabelEncoder
from final_model import *
from flask import Flask, render_template, flash, jsonify, redirect, url_for, session, request, logging
import cv2
from werkzeug.utils import secure_filename
import os
from flask import Flask, request, jsonify, redirect, url_for, session, render_template
import json
# initialize the app
app = Flask(__name__)

# Initialize the emotion detector
emotion_detector = FER()

# configure mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'backend'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = 'static/blog_images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# initialize mysql
mysql = MySQL(app)


@app.route("/")
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blogs WHERE is_public = TRUE ORDER BY created_at DESC LIMIT 4")
    blogs = cur.fetchall()
    
    cur.close()
   
    return render_template('index.html', blogs=blogs)

# Route for topic pages
@app.route('/anger-management')
def anger_management():
    return render_template('anger-management.html')


@app.route('/eating-disorders')
def eating_disorders():
    return render_template('eating-disorders.html')


@app.route('/depression')
def depression():
    return render_template('depression.html')


@app.route('/anxiety')
def anxiety():
    return render_template('anxiety.html')


@app.route('/trauma')
def trauma():
    return render_template('trauma.html')


@app.route('/grief')
def grief():
    return render_template('grief.html')


@app.route('/relationships')
def relationships():
    return render_template('relationships.html')


@app.route('/stress-management')
def stress_management():
    return render_template('stress-management.html')



#wrap to define if the user is currently logged in from session
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, please login.", "danger")
            return redirect(url_for('login'))
    return wrap

def log_in_user(username):
    users = Table("users", "name", "email", "username", "password")
    user = users.getone("username", username)

    session['logged_in'] = True
    session['username'] = username
    session['name'] = user.get('name')
    session['email'] = user.get('email')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    users = Table("users", "name", "email", "username", "password")
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        name = form.name.data
        
        if isnewuser(username):
            password = sha256_crypt.encrypt(form.password.data)
            users.insert(name, email, username, password)
            log_in_user(username)
            flash('You are now registered and logged in', 'success')
            return redirect(url_for('login'))
        else:
            flash('User already exists', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        candidate = request.form['password']

        users = Table("users", "name", "email", "username", "password")
        user = users.getone("username", username)
        accPass = user.get('password') if user else None

        if accPass is None:
            flash("Username is not found", 'danger')
            return redirect(url_for('login'))
        else:
            if sha256_crypt.verify(candidate, accPass):
                log_in_user(username)
                flash('You are now logged in.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid password", 'danger')
                return redirect(url_for('login'))

    return render_template('login.html')

# Dashboard route to display user's personal and public blogs
@app.route("/dashboard")
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    
    # Fetch personal blogs
    cur.execute("SELECT * FROM blogs WHERE username = %s ORDER BY created_at DESC", [session['username']])
    personal_blogs = cur.fetchall()
    
    
    
    cur.close()
    
    return render_template('dashboard.html', 
                           session=session, 
                           page='dashboard', 
                           all_blogs=personal_blogs)


@app.route('/edit_blog/<int:blog_id>', methods=['GET', 'POST'])
@is_logged_in
def edit_blog(blog_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blogs WHERE id = %s AND username = %s", (blog_id, session['username']))
    blog = cur.fetchone()

    if request.method == 'POST':
        title = request.form['blogTitle']
        content = request.form['blogContent']
        is_public = 'is_public' in request.form

        if 'blogImage' in request.files:
            image = request.files['blogImage']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
            else:
                image_path = blog['image_path']
        else:
            image_path = blog['image_path']

        cur.execute("UPDATE blogs SET title = %s, content = %s, image_path = %s, is_public = %s WHERE id = %s",
                    (title, content, image_path, is_public, blog_id))
        mysql.connection.commit()
        flash('Blog updated successfully', 'success')
        return redirect(url_for('dashboard'))

    cur.close()
    return render_template('edit_blog.html', blog=blog)
@app.route('/delete_blog/<int:blog_id>', methods=['POST'])
@is_logged_in
def delete_blog(blog_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM blogs WHERE id = %s AND username = %s", (blog_id, session['username']))
    mysql.connection.commit()
    cur.close()
    flash('Blog deleted successfully', 'success')
    return redirect(url_for('dashboard'))


# Logout route to clear session
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash("You have been logged out", "success")
    return redirect(url_for('index'))
@app.route("/quiz1")
def quiz1():    
    return render_template('quiz1.html')

@app.route("/quiz2")
def quiz2():    
    return render_template('quiz2.html')

@app.route("/quiz3")
def quiz3():    
    return render_template('quiz3.html')

@app.route("/quiz4")
def quiz4(): 
    return render_template('quiz4.html')

@app.route("/quiz5")
def quiz5():    
    return render_template('quiz5.html')

# @app.route("/questionnaire")
# def questionnaire():    
#     return render_template('quizDashboard.html')

@app.route("/solution1")
def solution1():    
    return render_template('solution1.html')

@app.route("/solution2")
def solution2():    
    return render_template('solution2.html')

@app.route("/solution3")
def solution3():    
    return render_template('solution3.html')

@app.route("/solution4")
def solution4():    
    return render_template('solution4.html')

@app.route("/solution5")
def solution5():    
    return render_template('solution5.html')

# @app.route("/solutiondash")
# def solutiondashboard():    
#     return render_template('solutionDashboard.html')

@app.route("/about")
def about():    
    return render_template('about.html')

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response = None
    if request.method == 'POST':
        df_input = request.form['question']
        df_input = get_text(df_input)
        print(df_input)
        tokenizer_t = joblib.load('tokenizer_t.pkl')
        vocab = joblib.load('vocab.pkl')
        df_input = remove_stop_words_for_input(tokenizer, df_input, 'questions')
        encoded_input = encode_input_text(tokenizer_t, df_input, 'questions')
        pred = get_pred(model1, encoded_input) 
        pred = bot_precausion(df_input, pred)
        response = get_response(df2, pred)
        print(response)
    return render_template('chatbot.html', response=response)

@app.route('/blog/<int:blog_id>', methods=['GET'])
def get_blog(blog_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blogs WHERE id = %s", [blog_id])
    blog = cur.fetchone()
    cur.close()

    if blog:
        return jsonify({
            'title': blog['title'],
            'content': blog['content'],
            'image_path': blog['image_path'],
            'author': blog['author']
        })
    else:
        return jsonify({'error': 'Blog not found'}), 404

@app.route('/view_more_blogs')
def view_more_blogs():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blogs WHERE is_public = TRUE ORDER BY created_at DESC")
    blogs = cur.fetchall()
   
    cur.close()
   
    return render_template('view_more_blogs.html', blogs=blogs)

# Renamed conflicting route to '/all_blogs'
@app.route('/all_blogs', methods=['GET'])
def all_blogs():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blogs WHERE is_public = TRUE ORDER BY created_at DESC")
    blogs = cur.fetchall()
    cur.close()
    return render_template('blogs.html', blogs=blogs)

@app.route('/my_blogs', methods=['GET'])
@is_logged_in
def my_blogs():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blogs WHERE username = %s ORDER BY created_at DESC", [session['username']])
    blogs = cur.fetchall()
    cur.close()
    return render_template('my_blogs.html', blogs=blogs)

@app.route('/submit_blog', methods=['POST'])
@is_logged_in
def submit_blog():
    title = request.form['blogTitle']
    content = request.form['blogContent']
    is_public = 'is_public' in request.form
    
    # Handle image upload
    if 'blogImage' in request.files:
        image = request.files['blogImage']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
        else:
            image_path = None
    else:
        image_path = None

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO blogs(title, content, image_path, author, username, is_public) VALUES(%s, %s, %s, %s, %s, %s)", 
                (title, content, image_path, session['name'], session['username'], is_public))
    mysql.connection.commit()
    cur.close()

    flash("Blog submitted successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route("/detect_emotion_redirect", methods=['GET'])
def detect_emotion_redirect():
    return redirect("http://127.0.0.1:5001/")
    

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
