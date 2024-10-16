from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# In-memory data structures
users = {}
updates = []
user_sessions = {}
user_post_times = {}

# List of common spam/fraud keywords
fraud_keywords = ['win', 'free', 'click', 'prize', 'money']

# User model
class User(UserMixin):
    def __init__(self, id, username, password, ip_address):
        self.id = id
        self.username = username
        self.password = password
        self.ip_address = ip_address

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route('/')
@login_required
def index():
    print(f"Current user: {current_user.username if current_user.is_authenticated else 'Not logged in'}")
    return render_template('index.html', updates=updates)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        for user in users.values():
            if user.username == username and user.password == password:
                login_user(user)
                return redirect(url_for('index'))
        
        flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ip_address = request.remote_addr

        if username in users:
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        # Check for existing users from the same IP address
        existing_users = sum(1 for user in users.values() if user.ip_address == ip_address)
        if existing_users >= 3:  # Threshold for multiple accounts
            flash('Multiple accounts detected from this IP address!')
            return redirect(url_for('register'))

        new_user = User(id=username, username=username, password=password, ip_address=ip_address)
        users[username] = new_user
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/post_update', methods=['POST'])
@login_required
def post_update():
    content = request.form['updateText']
    
    # Check for spam keywords
    if any(keyword in content.lower() for keyword in fraud_keywords):
        flash('Your post contains suspicious content and has been flagged!')
        return redirect(url_for('index'))
    # Create a post entry that includes the user's username
    updates.append({'user': current_user.username, 'content': content})
    return redirect(url_for('index'))
    # Check for posting frequency (e.g., more than 5 posts in 1 minute)
    user_id = current_user.id
    current_time = request.args.get('current_time')

    if user_id in user_post_times:
        recent_times = user_post_times[user_id]
        recent_times = [t for t in recent_times if t > current_time - 60]  # 60 seconds
        if len(recent_times) >= 5:  # More than 5 posts in the last minute
            flash('You are posting too frequently!')
            return redirect(url_for('index'))
        recent_times.append(current_time)
        user_post_times[user_id] = recent_times
    else:
        user_post_times[user_id] = [current_time]

    updates.append({'user': current_user.username, 'content': content})
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
