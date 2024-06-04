from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

# MySQL database connection configuration
db = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Chandrika1+",
    database="dating_app"
)
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        gender VARCHAR(10) NOT NULL,
        birthdate DATE NOT NULL,
        year INT,
        branch VARCHAR(50),
        degree VARCHAR(50),
        UNIQUE (username),
        INDEX (username)
    )
''')
db.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bio (
        bio_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        bio TEXT,
        FOREIGN KEY (username) REFERENCES users(username),
        UNIQUE (username),
        INDEX (username)
    )
''')
db.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS viewed_users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        viewer_username VARCHAR(255) NOT NULL,
        viewed_username VARCHAR(255) NOT NULL,
        FOREIGN KEY (viewer_username) REFERENCES users(username),
        FOREIGN KEY (viewed_username) REFERENCES users(username),
        UNIQUE (viewer_username, viewed_username)
    )
''')
db.commit()

@app.route('/')
def index():
    return render_template('dating_app.html')

@app.route('/save_bio', methods=['POST'])
def save_bio():
    username = session.get('username')
    if username:
        bio = request.form['bio']

        # Update user bio in the database
        query = "INSERT INTO bio (username, bio) VALUES (%s, %s) ON DUPLICATE KEY UPDATE bio = %s"
        values = (username, bio, bio)
        cursor.execute(query, values)
        db.commit()

    return redirect(url_for('success'))


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    birthdate = request.form['birthdate']
    year = request.form['year']
    branch = request.form['branch']
    degree = request.form['degree']

    # Insert data into the 'users' table
    query = "INSERT INTO users (username, email, password, gender, birthdate, year, branch, degree) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    values = (username, email, password, gender, birthdate, year, branch, degree)
    
    cursor.execute(query, values)
    db.commit()

    session['username'] = username  # Store username in session
    return redirect(url_for('success'))

@app.route('/signin', methods=['POST'])
def signin():
    signin_username = request.form['signin-username']
    signin_password = request.form['signin-password']

    # Check credentials against the 'users' table
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    values = (signin_username, signin_password)

    cursor.execute(query, values)
    user = cursor.fetchone()

    if user:
        session['username'] = signin_username  # Store username in session
        return redirect(url_for('success'))
    else:
        return render_template('signin_failed.html')

@app.route('/success')
def success():
    username = session.get('username')
    if username:
        # Fetch user details from the 'users' table
        query = "SELECT * FROM users WHERE username = %s"
        values = (username,)
        cursor.execute(query, values)
        user = cursor.fetchone()

        if user:
            user_details = {
                'username': user[1],
                'email': user[2],
                'gender': user[4],
                'birthdate': user[5],
                'year': user[6],
                'branch': user[7],
                'degree': user[8],
            }

            return render_template('success.html', username=username, user=user_details)

    return redirect(url_for('index'))

from random import choice

@app.route('/view_users', methods=['GET', 'POST'])
def view_users():
    if request.method == 'POST':
        preferred_year = request.form['preferred_year']
        preferred_branch = request.form['preferred_branch']
        preferred_gender = request.form['preferred_gender']

        # Get the currently logged-in username from the session
        current_username = session.get('username')

        # Fetch one random user with the specified preferences, excluding the currently logged-in user
        # and users who have already been viewed by the current user
        query_random_user = (
            "SELECT users.*, bio.bio FROM users "
            "LEFT JOIN bio ON users.username = bio.username "
            "WHERE year = %s AND branch = %s AND gender = %s AND users.username != %s "
            "AND users.username NOT IN (SELECT viewed_username FROM viewed_users WHERE viewer_username = %s) "
            "ORDER BY RAND() LIMIT 1"
        )
        values_random_user = (preferred_year, preferred_branch, preferred_gender, current_username, current_username)

        cursor.execute(query_random_user, values_random_user)
        random_user_data = cursor.fetchone()

        # Save the viewer and viewed information in the viewed_users table
        if random_user_data:
            viewer_username = current_username
            viewed_username = random_user_data[1]  # Assuming the username is in the second column

            # Check if the entry already exists to avoid duplicates
            query_check_duplicate = (
                "SELECT * FROM viewed_users WHERE viewer_username = %s AND viewed_username = %s"
            )
            values_check_duplicate = (viewer_username, viewed_username)

            cursor.execute(query_check_duplicate, values_check_duplicate)
            existing_entry = cursor.fetchone()

            if not existing_entry:
                # Insert the new entry
                query_save_viewed_user = (
                    "INSERT INTO viewed_users (viewer_username, viewed_username) VALUES (%s, %s)"
                )
                values_save_viewed_user = (viewer_username, viewed_username)

                cursor.execute(query_save_viewed_user, values_save_viewed_user)
                db.commit()

        return render_template('view_users.html', random_user=random_user_data, current_username=current_username)

    return redirect(url_for('index'))  # Redirect to home if it's a GET request



@app.route('/viewed_users', methods=['GET'])
def viewed_users():
    # Get the currently logged-in username from the session
    current_username = session.get('username')

    # Fetch viewed users for the current user from the viewed_users table
    query = "SELECT viewed_username FROM viewed_users WHERE viewer_username = %s"
    values = (current_username,)

    cursor.execute(query, values)
    viewed_users_data = cursor.fetchall()

    # Fetch details of the viewed users from the users table
    viewed_users_details = []
    for viewed_user_data in viewed_users_data:
        query_user = "SELECT * FROM users WHERE username = %s"
        values_user = (viewed_user_data[0],)

        cursor.execute(query_user, values_user)
        viewed_user = cursor.fetchone()

        if viewed_user:
            viewed_users_details.append({
                'username': viewed_user[1],
                'email': viewed_user[2],
                'gender': viewed_user[4],
                'birthdate': viewed_user[5],
                'year': viewed_user[6],
                'branch': viewed_user[7],
                'degree': viewed_user[8],
            })

    return render_template('viewed_users.html', viewed_users=viewed_users_details)
if __name__ == '__main__':
    app.run(debug=True)
