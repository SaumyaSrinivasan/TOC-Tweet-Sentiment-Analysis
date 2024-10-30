from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import mysql.connector
import time
import pandas as pd
import matplotlib.pyplot as plt
import io
from io import BytesIO
import base64
import seaborn as sns
import squarify
from wordcloud import WordCloud
from PIL import Image
import re
import os
import streamlit as st
from flask_mail import Mail, Message
import random
import string

import random

from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
from collections import Counter
#nltk.download('stopwords') - To uncomment and use only once at first run on any machine to download the packages
import matplotlib
matplotlib.use('Agg')  # Use the non-interactive backend
import subprocess  # Add this line



app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to the MySQL database
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root123',
    database='tweetdatabase'
)

# # Configure Flask-Mail for sending emails (replace with your email settings)
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587  # Use port 587 for TLS
# app.config['MAIL_USE_TLS'] = True  # Use TLS for secure communication
# app.config['MAIL_USE_SSL'] = False  # Do not use SSL


# mail = Mail(app)

# if 'keys' not in st.session_state:
#     st.session_state.keys = None  # Set the default value to None

# Initialize the variables
add_user_success = None
delete_user_success = None


# Setting the session timeout values
SESSION_TIMEOUT = 300  # 300 seconds (5 minutes) for initial session timeout
SESSION_EXTENSION = 180  # 180 seconds (3 minutes) for session extension


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = SESSION_TIMEOUT
    session.modified = True
    # Check if the user is still active
    if 'last_active' in session:
        current_time = time.time()
        last_active_time = session['last_active']
        time_since_last_active = current_time - last_active_time

        # If the user is still active, extend the session
        if time_since_last_active < SESSION_EXTENSION:
            session['last_active'] = current_time
        else:
            # Automatically log out the user if they are inactive for more than SESSION_EXTENSION
            session.pop('username', None)

 

@app.route('/', methods=['GET', 'POST'])
def index():
     if 'username' in session and session['username'] != 'admin': #remove after and <>
        return redirect(url_for('dashboard'))
     if request.method == 'POST':
        session['visits'] = 0
        return redirect(url_for('login'))

     return render_template('index.html')


# Generate a random token
def generate_verification_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=30))

# Store tokens in a dictionary (in-memory storage, for demonstration purposes)
verification_tokens = {}


# Customise your business logic here....



@app.route('/logout')
def logout():
    session['visits'] = 0
    session.pop('username', None)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)