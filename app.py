import gspread
from flask import Flask, render_template, request, redirect, url_for, session
import random
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------
# App Setup
# -------------------------

app = Flask(__name__)
app.secret_key = "change_this_secret_key_12345"

PASSWORD = "24/02/2025"   # <<< CHANGE THIS TO YOUR PASSWORD

# -------------------------
# Google Sheets Setup
# -------------------------
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

creds_json = os.environ.get("GOOGLE_CREDS")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

sheet = client.open("100ReasonsWhyBase")
messages_ws = sheet.worksheet("messages")
used_ws = sheet.worksheet("used_messages")

# -------------------------
# Login Required Helper
# -------------------------

def login_required():
    return session.get("logged_in")

# -------------------------
# Login Page (NEW)
# -------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        entered_password = request.form.get("password")

        if entered_password == PASSWORD:
            session["logged_in"] = True
            session.permanent = False
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="wrong password! :(")

    return render_template("login.html")

# -------------------------
# Home Page (NOW PROTECTED)
# -------------------------

@app.route("/", methods=["GET"])
def index():
    if not login_required():
        return redirect(url_for("login"))

    messages = messages_ws.col_values(1)
    return render_template("pick.html", messages_left=len(messages))

# -------------------------
# Pick a Message
# -------------------------

@app.route("/pick", methods=["POST"])
def pick():
    if not login_required():
        return redirect(url_for("login"))

    messages = messages_ws.col_values(1)

    if not messages:
        return render_template("pick.html", messages_left=0)

    chosen = random.choice(messages)

    used_ws.append_row([chosen])

    row_index = messages.index(chosen) + 1
    messages_ws.delete_rows(row_index)

    messages_left = len(messages) - 1

    return render_template(
        "pick.html",
        message=chosen,
        messages_left=messages_left
    )

# -------------------------
# Reset Messages (Popup First)
# -------------------------

@app.route("/reset", methods=["POST"])
def reset_popup():
    if not login_required():
        return redirect(url_for("login"))

    messages = messages_ws.col_values(1)
    return render_template(
        "pick.html",
        messages_left=len(messages),
        show_reload_popup=True
    )

# -------------------------
# Do Reset (Batch Transfer)
# -------------------------

@app.route("/do_reset", methods=["POST"])
def do_reset():
    if not login_required():
        return redirect(url_for("login"))

    used_messages = used_ws.col_values(1)

    if not used_messages:
        messages = messages_ws.col_values(1)
        return render_template(
            "pick.html",
            messages_left=len(messages)
        )

    rows_to_add = [[msg] for msg in used_messages]

    messages_ws.append_rows(rows_to_add)

    used_ws.clear()

    messages = messages_ws.col_values(1)

    return render_template(
        "pick.html",
        messages_left=len(messages),
        popup_reset=True
    )

# -------------------------
# Logout (NEW)
# -------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------------

if __name__ == "__main__":
    app.run(debug=True)