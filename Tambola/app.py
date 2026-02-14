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

def generate_full_sheet():
    all_nums = list(range(1, 91))
    random.shuffle(all_nums)
    sheet = []
    for i in range(6):
        ticket = [[None for _ in range(9)] for _ in range(3)]
        ticket_nums = sorted(all_nums[i*15 : (i+1)*15])
        for num in ticket_nums:
            col = (num - 1) // 10 if num <= 89 else 8
            for row in range(3):
                if ticket[row][col] is None:
                    ticket[row][col] = num
                    break
        sheet.append(ticket)
    return sheet

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
        token = str(uuid.uuid4())
        users[token] = {"tickets": generate_full_sheet(), "phone": phone}
        game_url = f"https://h-game.onrender.com/user/{token}"
        msg = f"Hello! Your Tambola Full Sheet (6 Tickets) is ready. All numbers 1-90 are included. Play here: {game_url}"
        whatsapp_link = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
        return render_template("admin_dashboard.html", whatsapp_link=whatsapp_link)
    return render_template("admin_dashboard.html")

@app.route("/user/<token>")
def user_page(token):
    user = users.get(token)
    if not user: return "Invalid Ticket"
    return render_template("user_ticket.html", tickets=user["tickets"], called_numbers=called_numbers)

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
    return jsonify({"number":num, "winners": winners, "all_called": called_numbers})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
