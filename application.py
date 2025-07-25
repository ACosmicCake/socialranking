import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology,convert,people
from lists import countries,questions,answer,income_groups


# Configure application
app = Flask(__name__)

app.jinja_env.filters["convert"] = convert
app.jinja_env.filters["people"] = people


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True



# Ensure responses aren't cached
@app.after_request
def after_request(response):
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database



@app.route("/")
def index():
    """HOMEPAGE"""
    session['currentquestion'] = -1
    session['country'] = 0
    session['education'] = 0
    session['wealth'] = 0
    session['access'] = 0
    session['result'] = 0
    return render_template("index.html",)


@app.route("/quiz",methods=["GET", "POST"])
def quiz():
    if request.method == "POST":

        #itterate through questions everytimr the user clicks next
        currentquestion = session['currentquestion']
        currentquestion = currentquestion + 1
        session['currentquestion'] = currentquestion


        # Get the country from the form
        country = request.form.get("country")

        # Get the income group for the selected country
        income_group = ""
        for group, countries_in_group in income_groups.items():
            if country in countries_in_group:
                income_group = group
                break

        # Store the income group in the session
        session['country'] = income_group

        if currentquestion == 0 or currentquestion == 1 or currentquestion == 2 or currentquestion == 3 or currentquestion == 4 or currentquestion == 5:
            if request.form.get("radio-stacked") != None:
                questionpoint = request.form.get("radio-stacked")
                session['access'] += int(questionpoint)
        if currentquestion == 6:
            if request.form.get("radio-stacked") != None:
                session['access'] = session['access']/5
                questionpoint = request.form.get("radio-stacked")
                session['access'] = (int(questionpoint) + session['access'])/2
        if currentquestion == 7:
            if request.form.get("radio-stacked") != None:
                questionpoint = request.form.get("radio-stacked")
                session['education'] = int(questionpoint)
        if currentquestion == 8:
            if request.form.get("radio-stacked") != None:
                questionpoint = request.form.get("radio-stacked")
                session['wealth'] = int(questionpoint)
                # Create a dictionary to hold the results
                result = {
                    'wealth': session['wealth'],
                    'education': session['education'],
                    'access': session['access'],
                    'country': session['country']
                }
                return render_template("detailed.html", result=result)


        return render_template("quiz.html",questions=questions, count=currentquestion, answer = answer)

    else:
        session['currentquestion'] = -1
        session['country'] = 0
        session['education'] = 0
        session['wealth'] = 0
        session['access'] = 0
        session['result'] = 0
        return render_template("quizcountry.html",countries=countries)



@app.route("/about")
def about():
    """Display the quiz"""
    return render_template("about.html",)

@app.route("/faq")
def faq():
    """Display the quiz"""

    return render_template("faq.html",)

@app.route("/creator")
def creator():
    """Display the quiz"""

    return render_template("creator.html",)

@app.route("/source")
def source():
    """Display the quiz"""

    return render_template("source.html",)

@app.route("/result", methods=["GET", "POST"])
def result():
    """Display the quiz results."""
    result = {
        'wealth': session.get('wealth'),
        'education': session.get('education'),
        'access': session.get('access'),
        'country': session.get('country')
    }
    return render_template("detailed.html", result=result)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
