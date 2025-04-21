from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# ------------------ DATABASE SETUP ------------------

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, password TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ------------------ FOOD CHAIN DATA ------------------

ecosystems = {
    "Forest": {
        "chain": [
            {"name": "Grass", "role": "Producer"},
            {"name": "Grasshopper", "role": "Primary Consumer"},
            {"name": "Frog", "role": "Secondary Consumer"},
            {"name": "Snake", "role": "Tertiary Consumer"},
            {"name": "Eagle", "role": "Apex Predator"}
        ]
    },
    "Ocean": {
        "chain": [
            {"name": "Phytoplankton", "role": "Producer"},
            {"name": "Zooplankton", "role": "Primary Consumer"},
            {"name": "Small Fish", "role": "Secondary Consumer"},
            {"name": "Tuna", "role": "Tertiary Consumer"},
            {"name": "Shark", "role": "Apex Predator"}
        ]
    }
}

# ------------------ HTML TEMPLATES ------------------

layout = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Visualization of Food Chain</title>
  <style>
    body { font-family: Arial, sans-serif; background-color: #f0f9f0; margin: 0; padding: 0; }
    header { background: #2e7d32; color: white; padding: 20px; text-align: center; }
    main { padding: 20px; max-width: 900px; margin: auto; }
    .form-box { background: #e8f5e9; padding: 20px; border-radius: 10px; }
    input, button { padding: 10px; margin: 5px 0; width: 100%; }
    button { background-color: #4caf50; color: white; border: none; }
    button:hover { background-color: #388e3c; cursor: pointer; }
    .species-box { background: white; border-left: 5px solid #388e3c; padding: 10px; margin: 10px; border-radius: 5px; display: inline-block; min-width: 120px; text-align: center; }
    .arrow { display: inline-block; font-size: 24px; margin: 0 10px; }
  </style>
</head>
<body>
  <header><h1>Visualization of Food Chain</h1></header>
  <main>
    {% block content %}{% endblock %}
  </main>
</body>
</html>
"""

# ------------------ ROUTES ------------------

@app.route('/')
def welcome():
    return render_template_string(layout + """
    {% block content %}
    <div class='form-box'>
      <h2>Register to Explore Food Chains</h2>
      <form method='POST' action='/register'>
        <input type='text' name='name' placeholder='Your Name' required>
        <input type='email' name='email' placeholder='Email' required>
        <input type='password' name='password' placeholder='Password' required>
        <button type='submit'>Register</button>
      </form>
      <p>Already registered? <a href='/login'>Login here</a></p>
    </div>
    {% endblock %}
    """)

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
    conn.commit()
    conn.close()
    
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT id, name, password FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user'] = {'id': user[0], 'name': user[1]}
            return redirect(url_for('visualization'))
        else:
            return "<h3>Invalid credentials. <a href='/login'>Try again</a></h3>"

    return render_template_string(layout + """
    {% block content %}
    <div class='form-box'>
      <h2>Login</h2>
      <form method='POST'>
        <input type='email' name='email' placeholder='Email' required>
        <input type='password' name='password' placeholder='Password' required>
        <button type='submit'>Login</button>
      </form>
    </div>
    {% endblock %}
    """)

@app.route('/visualization')
def visualization():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template_string(layout + """
    {% block content %}
    <h2>Welcome, {{ session['user']['name'] }}!</h2>
    <p>Select an ecosystem to visualize its food chain:</p>
    <select id='ecosystem-select'>
      {% for name in ecosystems %}<option value='{{ name }}'>{{ name }}</option>{% endfor %}
    </select>
    <div id='food-chain-container'></div>
    <button onclick='exportAsPDF()'>Export as PDF</button>
    <button onclick='exportAsImage()'>Export as Image</button>

    <script src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'></script>
    <script src='https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'></script>
    <script>
      const data = {{ ecosystems | tojson }};
      const select = document.getElementById('ecosystem-select');
      const container = document.getElementById('food-chain-container');

      function renderChain(name) {
        container.innerHTML = '';
        const chain = data[name].chain;
        chain.forEach((item, i) => {
          container.innerHTML += `<div class='species-box'><b>${item.name}</b><br><em>${item.role}</em></div>`;
          if (i < chain.length - 1) container.innerHTML += `<span class='arrow'>→</span>`;
        });
      }
      select.addEventListener('change', () => renderChain(select.value));
      window.onload = () => renderChain(select.value);

      async function exportAsPDF() {
        const { jsPDF } = window.jspdf;
        const canvas = await html2canvas(container);
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF();
        pdf.addImage(imgData, 'PNG', 10, 10, 180, 60);
        pdf.save('food_chain.pdf');
      }

      async function exportAsImage() {
        const canvas = await html2canvas(container);
        const link = document.createElement('a');
        link.download = 'food_chain.png';
        link.href = canvas.toDataURL();
        link.click();
      }
    </script>
    {% endblock %}
    """, ecosystems=ecosystems)

@app.route('/admin')
def admin():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, name, email FROM users")
    users = c.fetchall()
    conn.close()

    return render_template_string(layout + """
    {% block content %}
    <h2>Admin Panel - Registered Users</h2>
    <ul>
      {% for user in users %}
        <li><b>{{ user[1] }}</b> ({{ user[2] }})</li>
      {% endfor %}
    </ul>
    {% endblock %}
    """, users=users)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('welcome'))

@app.route('/api/ecosystem/<name>')
def get_ecosystem(name):
    return jsonify(ecosystems.get(name, {}))

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

