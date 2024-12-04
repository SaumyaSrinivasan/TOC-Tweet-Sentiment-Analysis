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
import matplotlib



app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to the MySQL database
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root123',
    database='tweetdatabase'
)

# Configure Flask-Mail for sending emails (replace with your email settings)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # Use port 587 for TLS
app.config['MAIL_USE_TLS'] = True  # Use TLS for secure communication
app.config['MAIL_USE_SSL'] = False  # Do not use SSL


mail = Mail(app)

if 'keys' not in st.session_state:
    st.session_state.keys = None  # Set the default value to None

# Initialize the variables
add_user_success = None
delete_user_success = None


# Setting the session timeout values
SESSION_TIMEOUT = 300  # 300 seconds (5 minutes) for initial session timeout
SESSION_EXTENSION = 180  # 180 seconds (2 minutes) for session extension


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



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    #check if signup first time
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        toc_name = request.form.get('toc_name')

        # Insert user data into the database
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (username, email, password, toc_name) VALUES (%s, %s, %s, %s)',
                       (username, email, password, toc_name))
        db.commit()
        # Generate a verification token
        verification_token = generate_verification_token()

        # Store the token in the dictionary (replace with a database in production)
        verification_tokens[email] = verification_token

        # Send a verification email
        msg = Message('Verify Your Email', sender='atoc3680@gmail.com', recipients=[email])
        verification_link = url_for('verify', token=verification_token, _external=True)
        msg.body = f'Click the following link to verify your email: {verification_link}'
        mail.send(msg)

        flash('A verification link has been sent to your email. Please click it to complete the registration.')


        # Redirect to the login page
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/verify/<token>', methods=['GET'])
def verify(token):
    if 'username' in session:
        return redirect(url_for('dashboard'))

    # Check if the token matches a stored token
    for email, stored_token in verification_tokens.items():
        if token == stored_token:
            # Verification successful
            flash('Email verification successful! You can now log in.')
            
            # Remove the verified email and token from the dictionary (replace with database update)
            del verification_tokens[email]

            return redirect(url_for('login'))

    flash('Invalid verification token. Please try again or request a new verification link.')

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.setdefault('visits', 0)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        session['visits'] += 1
    
        # Check the username and password against the database
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        
        user = cursor.fetchone()

        if username == 'admin' and password == 'admin':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))

        if username != 'admin' and user and toc_name == user[3]:
           
            session['toc_name'] = toc_name
            # Check if the user is the admin
            if username == 'admin':
                session['username'] = 'admin'
            else:
                session['username'] = username
            return redirect(url_for('dashboard'))
        
        else:
           session['login_attempts'] = session.get('login_attempts', 0) + 1
           login_attempts = session['login_attempts']
           alert_message = "Invalid username or password. Please try again."

           # Pass the alert message and login attempts count to the template
           return render_template('login', alert_message=alert_message, login_attempts=login_attempts)
                
    return render_template('login.html')



@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if session.get('admin'):
        if request.method == 'POST':
            cursor = db.cursor()
            delete_user_success = 'false'
            add_user_success = 'false'

            # Handle adding a user
            if 'new_username' in request.form and 'new_email' in request.form \
                    and 'new_password' in request.form and 'new_toc_name' in request.form:
                new_username = request.form.get('new_username')
                new_email = request.form.get('new_email')
                new_password = request.form.get('new_password')
                new_toc_name = request.form.get('new_toc_name')

                cursor.execute(
                    'INSERT INTO users (username, email, password, toc_name) VALUES (%s, %s, %s, %s)',
                    (new_username, new_email, new_password, new_toc_name))
                
                add_user_success = 'true'
                db.commit()

            # Handle deleting a user
            if 'username_to_delete' in request.form:
                username_to_delete = request.form.get('username_to_delete')
                cursor.execute('DELETE FROM users WHERE username = %s', (username_to_delete,))
                delete_user_success='true'
                db.commit()

            cursor.execute('SELECT * FROM users')
            users = cursor.fetchall()

            cursor.close()
            
            return render_template('admin_dashboard', users=users, add_user_success=add_user_success, delete_user_success=delete_user_success)

        # Fetch all user details from the database
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()

        return render_template('admin_dashboard.html', users=users)

    # If not an admin, redirect to login
    return redirect(url_for('login'))



@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in
    if 'username' in session:
        username = session['user']
        # Store the 'toc_name' in session
        toc_name = session['toc_name']
        return render_template('dashboard', username=username)
    else:
        return redirect(url_for('login'))
    

@app.route('/sentiment-data')
def sentiment_data():
    if 'username' in session:
        if request.method == 'POST':
            # Handle the form submission for year selection
            selected_year = int(request.form.get('year'))  # Get selected year from the user
        else:
            selected_year = None  # Default to None if the form is not submitted yet

        toc_name = session['toc_name']  # Get the toc_name from the session
        
        # Query data from the MySQL table sentiment_data
        cursor = db.cursor()
        cursor.execute('SELECT * FROM sentiment_data')
        data = cursor.fetchall()
        cursor.execute('SELECT * FROM sentiment_data WHERE toc_name = %s', (toc_name,))
        toc_data = cursor.fetchall()

        if not data:
            return "No data found for this TOC."
        
        # Convert the data to a pandas DataFrame
        data = pd.DataFrame(data, columns=['user_handle', 'tweet_text', 'toc_name', 'tweet_date', 'Day', 'Month','Year', 'hashtags',
                                           'processed_tweet_text', 'Polarity', 'Sentiment_Category' ])
        toc_data = pd.DataFrame(toc_data, columns=['user_handle', 'tweet_text', 'toc_name', 'tweet_date', 'Day', 'Month','Year', 'hashtags',
                                           'processed_tweet_text', 'Polarity', 'Sentiment_Category' ])

        overall_fig, overall_ax = plt.subplots()

        # Overall Sentiment Pie Chart
        plt.figure(figsize=(6, 6))
        data['Sentiment_Category'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['red', 'green', 'gray'])
        # plt.title('Overall Sentiment of Users')
        plt.axis('equal')
        plt.savefig(overall_img_buffer, format='png')
        plt.close(overall_fig)

        # TOC-Specific Sentiment Pie Chart
        plt.figure(figsize=(6, 6))
        toc_specific_fig, toc_specific_ax = plt.subplots()
        toc_data['Sentiment_Category'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['pink', 'blue', 'yellow'])
        # plt.title(f'{toc_name} Sentiment')
        plt.axis('equal')
        toc_specific_img_buffer = io.BytesIO()
        plt.savefig(toc_specific_img_buffer, format='png')
        plt.close(toc_specific_fig)

        # Generate Sentiment Stacked Bar Chart for each year
        stacked_bar_fig, stacked_bar_ax = plt.subplots(figsize=(8, 6))
        sns.countplot(x='Sentiment_Category', hue='Year', data=data[data['toc_name'] == toc_name], palette='Set2')
        plt.title(f'Sentiment Distribution of User Tweets on {toc_name} by Year')
        plt.xlabel('Sentiment Category')
        # Save the stacked bar chart to an in-memory buffer
        stacked_bar_img_buffer = io.BytesIO()
        plt.savefig(stacked_bar_img_buffer, format='png')
        plt.close(stacked_bar_fig)

        # Convert images to base64-encoded strings
        overall_img_data = base64.b64encode(overall_img_buffer.getvalue()).decode('utf-8')
        stacked_bar_img_data = base64.b64encode(stacked_bar_img_buffer.getvalue()).decode('utf-8')

        # Line Graph Generation
        if selected_year is not None:
            # Group data by month and count the number of tweets for each month in the selected year
            time_series_data = toc_data[toc_data['Year'] == selected_year].groupby('Month').size()

            # Plot the line graph
            line_graph_fig, line_graph_ax = plt.subplots(figsize=(8, 6))
            plt.plot(time_series_data.index, time_series_data.values, marker='o', linestyle='-', color='green')
            plt.title(f'Number of Tweets for {toc_name} in {selected_year}')
            plt.xlabel('Month')
            plt.ylabel('Number of Tweets')
            plt.grid(True)
            
            # Save the line graph to an in-memory buffer
            line_graph_img_buffer = io.BytesIO()
            plt.savefig(line_graph_img_buffer, format='png')
            plt.close(line_graph_fig)

            # Convert the line graph image to a base64-encoded string
            line_graph_img_data = base64.b64encode(line_graph_img_buffer.getvalue()).decode('utf-8')

        else:
            line_graph_img_data = None

        cursor.close()

        return render_template('sentiment.html', overall_img_data=overall_img_data, toc_img_data=toc_specific_img_data, 
                               stacked_bar_img_data=stacked_bar_img_data, line_graph_img_data=line_graph_img_data)


    else:
        return redirect(url_for('login'))
    

# Create a new route to display line graph
@app.route('/line-graph', methods=['POST'])
def line_graph():
    if 'username' in session:
        selected_year = request.form.get('year')
        if selected_year is not None:
            selected_year = int(selected_year)
        
        else:
             # Handling the case when 'year' is not provided in the form data
             selected_year = None

        toc_name = session['toc_name']  # Get the toc_name from the session
        selected_year = int(request.form.get('year'))  # Get selected year from the user
        
        # Query data from the MySQL table sentiment_data for the selected TOC and year
        cursor = db.cursor()
        cursor.execute('SELECT * FROM sentiment_data WHERE toc_name = %s AND Year = %s', (toc_name, selected_year))
        toc_year_data = cursor.fetchall()

        if not toc_year_data:
            return "No data found for this TOC and year."

        # Convert the data to a pandas DataFrame
        toc_year_data = pd.DataFrame(toc_year_data, columns=['user_handle', 'tweet_text', 'toc_name', 'tweet_date', 'Day', 'Month','Year', 'hashtags',
                                           'processed_tweet_text', 'Polarity', 'Sentiment_Category'])

        # Group data by month and count the number of tweets for each month
        time_series_data = toc_year_data.groupby('Month').size()

        # Plot the line graph
        plt.figure(figsize=(8, 4))
        plt.plot(time_series_data.index, time_series_data.values, marker='o', linestyle='-', color='green')
        plt.title(f'Number of Tweets for {toc_name} in {selected_year}')
        plt.xlabel('Month')
        plt.ylabel('Number of Tweets')
        plt.grid(True)

        # Save the plot as an image (optional)
        plt.savefig('static/line_graph.png')

        # Convert the image to a base64-encoded string
        line_graph_img_data = base64.b64encode(open('static/line_graph.png', 'rb').read()).decode('utf-8')

        cursor.close()

        return render_template('line_graph.html', line_graph_img_data=line_graph_img_data)
    else:
        return redirect(url_for('login'))




@app.route('/topic')
def topic_analysis():
    if 'username' in session:
        toc_name = session['toc_name']  # Get the toc_name from the session
        
        # Query data from the MySQL table sentiment_data
        cursor = db.cursor()
        cursor.execute('SELECT * FROM sentiment_data')
        data = cursor.fetchall()
        cursor.execute('SELECT * FROM sentiment_data WHERE toc_name = %s', (toc_name,))
        toc_data = cursor.fetchall()
        

        if not data:
            return "No data found for this TOC."
        
        # Convert the data to a pandas DataFrame
        data = pd.DataFrame(data, columns=[ 'user_handle', 'tweet_text', 'toc_name', 'tweet_date', 'Day', 'Month','Year', 'hashtags',
                                           'processed_tweet_text', 'Polarity', 'Sentiment_Category' ])
        toc_data = pd.DataFrame(toc_data, columns=['user_handle', 'tweet_text', 'toc_name', 'tweet_date', 'Day', 'Month','Year', 'hashtags',
                                           'processed_tweet_text', 'Polarity', 'Sentiment_Category' ])

        # Generate Word Cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords.words('english')).generate(' '.join(toc_data['tweet_text']))
        plt.figure(figsize=(8, 4))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        # Save the word cloud to an in-memory buffer
        wordcloud_img_buffer = io.BytesIO()
        plt.savefig(wordcloud_img_buffer, format='png')
        plt.close()

        # Convert the image to a base64-encoded string
        wordcloud_img_data = base64.b64encode(wordcloud_img_buffer.getvalue()).decode('utf-8')

        # Get Top 10 Tweets
        tweet_counts = toc_data['tweet_text'].value_counts().reset_index()
        tweet_counts.columns = ['tweet_text', 'frequency']
        tweet_counts = tweet_counts.sort_values(by='frequency', ascending=False)
        top_10_tweets = tweet_counts.head(10)
        
        # Save bar chart to an in-memory buffer
        plt.figure(figsize=(15, 5))
        sns.barplot(x=list(range(1, 11)), y='frequency', data=top_10_tweets, palette='viridis')
        plt.title('Top 10 Most Frequent Tweets by Users')
        plt.xlabel('Tweet Number')
        plt.ylabel('Frequency')
        top_tweets_img_buffer = io.BytesIO()
        plt.savefig(top_tweets_img_buffer, format='png')
        plt.close()

        # Convert the bar chart image to a base64-encoded string
        top_tweets_img_data = base64.b64encode(top_tweets_img_buffer.getvalue()).decode('utf-8')

        tweet_counts = toc_data['tweet_text'].value_counts().reset_index()
        tweet_counts.columns = ['tweet_text', 'frequency']

        tweet_counts = tweet_counts.sort_values(by='frequency', ascending=False)

        top_10_tweets = tweet_counts.head(10)

        top_10_tweets_list = [
            {'tweet_text': row['tweet_text'], 'frequency': row['frequency']}
            for index, row in top_10_tweets.iterrows()
        ]

        # Frequent Hashtags Bar Chart
        hashtag_counts = toc_data['hashtags'].str.split().explode().value_counts()
        
        # Exclude the TOC name if it is present in the hashtags
        toc_name_pattern = re.compile(r'\b#' + re.escape(toc_name) + r'\b', flags=re.IGNORECASE)
        hashtag_counts.index = hashtag_counts.index.map(lambda hashtag: re.sub(toc_name_pattern, '', hashtag))


       # Selecting top 10 hashtags
        top_10_hashtags = hashtag_counts.nlargest(10)
    
        size = top_10_hashtags.values.tolist()

        # Step 3: Visualizing the top used hashtags for the specified TOC as a treemap using squarify
        plt.figure(figsize=(10, 6))
        squarify.plot(sizes=size, label=top_10_hashtags.index, alpha=0.5)
        plt.title(f'Top 10 Hashtags for {toc_name}')
        plt.axis('off')
        plt.show()

        hashtag_img_buffer = io.BytesIO()
        plt.savefig(hashtag_img_buffer, format='png')
        hashtag_img_buffer.seek(0)
        hashtag_img_data = base64.b64encode(hashtag_img_buffer.read()).decode('utf-8')

        cursor.close()
        return render_template('topic.html', wordcloud_img_data=wordcloud_img_data, top_tweets_img_data=top_tweets_img_data, top_10_tweets=top_10_tweets_list, hashtag_img_data=hashtag_img_data)
      
    
    else:
        return redirect(url_for('login'))
    

@app.route('/cause')
def cause():
    # Checking if the user is logged in
    if 'username' in session:
        username = session['username']
        toc_name = session['toc_name']  # Get the TOC name from the session

        # Set the TOC_NAME environment variable for the Streamlit process
        os.environ['TOC_NAME'] = toc_name
       
        
        # To Run the Streamlit dashboard as a separate process
        streamlit_process = subprocess.Popen(['data', 'run', 'filename'])  #causeId_dashboards.py is the streamlit dashboard created

        streamlit_process.wait()
        return render_template('dashboard.html', username=username)
    
    else:
        return redirect(url_for('login'))
    

# Defining the route for the recommendation page
@app.route('/recommendation')
def recommendation():
    # Checking if the user is logged in
    if 'username' in session:
        username = session['username']
        toc_name = session['toc_name']  # Get the TOC name from the session
       
        # Launch the Streamlit application as a subprocess
        streamlit_process = subprocess.Popen(["data", "run", "filename"])
        streamlit_process.wait()
        return render_template('dashboard', username=username)
    
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session['visits'] = 0
    session.pop('username', None)
    return render_template('index')


if __name__ == '__main__':
    app.run(debug=True)
