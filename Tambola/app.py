from flask import Flask, render_template, request, redirect, session, jsonify
import random
import uuid
import urllib.parse
import os

app = Flask(__name__)
app.secret_key = "secret123"

users = {}
called_numbers = []
remaining_numbers = list(range(1, 91))

winners = {
    "first_five": [],
    "top_line": [],
    "middle_line": [],
    "bottom_line": [],
    "full_house": []
}

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def generate_ticket():
    ticket = [[None for _ in range(9)] for _ in range(3)]
    columns = {i: list(range(i*10 if i>0 else 1, (i+1)*10 if i<8 else 91)) for i in range(9)}
    filled = 0
    while filled < 15:
        col = random.randint(0,8)
        row = random.randint(0,2)
        if ticket[row][col] is None:
            n = random.choice(columns[col])
            all_nums = [num for r in ticket for num in r if num]
            if n not in all_nums:
                ticket[row][col] = n
                filled += 1
    return ticket

def check_all_winners():
    for token, data in users.items():
        phone = data["phone"]
        for idx, ticket in enumerate(data["tickets"]):
            ticket_label = f"Ph: {phone} (T#{idx+1})"
            all_nums = [n for r in ticket for n in r if n]
            marked = [n for n in all_nums if n in called_numbers]

            if len(marked) >= 5 and ticket_label not in winners["first_five"]:
                winners["first_five"].append(ticket_label)
            
            line_keys = ["top_line", "middle_line", "bottom_line"]
            for i in range(3):
                row_nums = [n for n in ticket[i] if n]
                if row_nums and all(n in called_numbers for n in row_nums):
                    if ticket_label not in winners[line_keys[i]]:
                        winners[line_keys[i]].append(ticket_label)
            
            if len(marked) == 15 and ticket_label not in winners["full_house"]:
                winners["full_house"].append(ticket_label)

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
    return render_template("admin_login.html")

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "admin" not in session: return redirect("/")
    whatsapp_link = None
    if request.method == "POST":
        phone = request.form.get("phone")
        count = int(request.form.get("ticket_count", 1))
        token = str(uuid.uuid4())
        users[token] = {"tickets": [generate_ticket() for _ in range(count)], "phone": phone}
        
        # ఇక్కడ మీ లైవ్ లింక్ అప్‌డేట్ చేయబడింది
        game_url = f"https://h-game.onrender.com/user/{token}"
        msg = f"నమస్తే! మీ తంబోలా టికెట్లు రెడీ. మొత్తం {count} టికెట్లు ఉన్నాయి. ఆడటానికి ఇక్కడ క్లిక్ చేయండి: {game_url}"
        whatsapp_link = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
        return render_template("admin_dashboard.html", whatsapp_link=whatsapp_link)
    return render_template("admin_dashboard.html")

@app.route("/user/<token>")
def user_page(token):
    user = users.get(token)
    if not user: return "Invalid Ticket"
    return render_template("user_ticket.html", tickets=user["tickets"])

@app.route("/game")
def game():
    return render_template("game.html")

@app.route("/call_number")
def call_number():
    if not remaining_numbers: return jsonify({"number":"Game Over"})
    num = random.choice(remaining_numbers)
    remaining_numbers.remove(num)
    called_numbers.append(num)
    check_all_winners()
    return jsonify({"number":num, "winners": winners})

if __name__ == "__main__":
    # Render కోసం పోర్ట్ సెట్టింగ్
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)