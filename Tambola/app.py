from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import uuid
import urllib.parse
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Game State
called_numbers = []
users = {}

def generate_tambola_ticket():
    ticket = [[0 for _ in range(9)] for _ in range(3)]
    for row in range(3):
        cols = random.sample(range(9), 5)
        for col in cols:
            num = random.randint(col * 10 + 1, col * 10 + 10)
            ticket[row][col] = num
    return ticket

@app.route('/')
def admin_login():
    return render_template('admin_login.html')

# ఇక్కడ మెథడ్స్ అప్‌డేట్ చేశాను - దీనివల్ల ఎర్రర్ రాదు
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return "Invalid Credentials"
    return redirect(url_for('admin_login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    # అడ్మిన్ డాష్‌బోర్డ్ లో కాల్ చేసిన నంబర్లు కూడా కనిపిస్తాయి
    return render_template('admin_dashboard.html', called_numbers=called_numbers)

@app.route('/generate_tickets', methods=['POST'])
def generate_tickets():
    phone = request.form.get('phone')
    try:
        # అడ్మిన్ డాష్‌బోర్డ్ నుండి వచ్చే టికెట్ సంఖ్యను తీసుకుంటుంది
        count = int(request.form.get('ticket_count', 6)) 
    except:
        count = 6
        
    token = str(uuid.uuid4())[:8]
    user_tickets = []
    for _ in range(count):
        user_tickets.append(generate_tambola_ticket())
        
    users[token] = {"phone": phone, "tickets": user_tickets}
    
    base_url = request.url_root.rstrip('/')
    link = f"{base_url}/ticket/{token}"
    msg = f"Hello! Here are your {count} Tambola Tickets: {link}"
    whatsapp_url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
    return redirect(whatsapp_url)

@app.route('/ticket/<token>')
def show_ticket(token):
    user_data = users.get(token)
    if not user_data:
        return "Ticket Not Found"
    # యూజర్ టికెట్ పేజీకి పిలిచిన నంబర్ల లిస్ట్ పంపిస్తున్నాము
    return render_template('user_ticket.html', tickets=user_data['tickets'], called_numbers=called_numbers)

@app.route('/call_number', methods=['POST'])
def call_number():
    if len(called_numbers) >= 90:
        return jsonify({"status": "over"})
    
    new_num = random.randint(1, 90)
    while new_num in called_numbers:
        new_num = random.randint(1, 90)
    
    called_numbers.append(new_num)
    # కొత్త నంబర్ మరియు మొత్తం హిస్టరీని రిటర్న్ చేస్తుంది
    return jsonify({"number": new_num, "history": called_numbers})

if __name__ == '__main__':
    app.run(debug=True)
