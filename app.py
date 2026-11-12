from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "smhs_secure_secret_key_2026"  # Secures user sessions

# Mock User Database for testing (Will be replaced with live cloud DB upon acceptance)
USERS = {
    "headteacher": {
        "password": "SMHSPassword2026!",
        "role": "HEAD_TEACHER",
        "name": "Head Teacher",
    },
    "bursar": {
        "password": "SMHSPassword2026!",
        "role": "BURSAR",
        "name": "School Bursar",
    },
    "dos": {
        "password": "SMHSPassword2026!",
        "role": "DOS",
        "name": "Director of Studies",
    },
}


@app.route("/", methods=["GET", "POST"])
def login():
  error = None
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    if username in USERS and USERS[username]["password"] == password:
      session["user"] = username
      session["role"] = USERS[username]["role"]
      session["name"] = USERS[username]["name"]
      return redirect(url_for("dashboard"))
    else:
      error = "Invalid credentials. Access Denied."

  return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
  if "user" not in session:
    return redirect(url_for("login"))
  return render_template(
      "dashboard.html",
      name=session["name"],
      role=session["role"],
  )


@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("login"))


if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=5000)
