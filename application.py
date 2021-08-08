import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology,convert,people
from lists import countries,questions,answer,lowincome,lowmiddleincome,uppermiddleincome,highincome
import lists



# Configure application
app = Flask(__name__)

app.jinja_env.filters["convert"] = convert
app.jinja_env.filters["people"] = people


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True



# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database



@app.route("/")
def index():
    """HOMEPAGE"""
    lists.currentquestion = -1
    lists.country = 0
    lists.education = 0
    lists.wealth = 0
    lists.access = 0
    lists.result = 0
    return render_template("index.html",)


@app.route("/quiz",methods=["GET", "POST"])
def quiz():
    if request.method == "POST":

        #itterate through questions everytimr the user clicks next
        currentquestion = lists.currentquestion
        currentquestion = currentquestion + 1
        lists.currentquestion = currentquestion


        # get the GNI capita of the users country
        country = request.form.get("country")
        if country in highincome:
            lists.country = 16
        if country in uppermiddleincome:
            lists.country = 51
        if country in lowmiddleincome:
            lists.country = 91
        if country in lowincome:
            lists.country = 100

        if currentquestion == 0 or currentquestion == 1 or currentquestion == 2 or currentquestion == 3 or currentquestion == 4 or currentquestion == 5:
            if request.form.get("radio-stacked") != None:
                questionpoint = request.form.get("radio-stacked")
                lists.access += int(questionpoint)
        if currentquestion == 6:
            if request.form.get("radio-stacked") != None:
                lists.access = lists.access/5
                questionpoint = request.form.get("radio-stacked")
                lists.access = (int(questionpoint) + lists.access)/2
        if currentquestion == 7:
            if request.form.get("radio-stacked") != None:
                questionpoint = request.form.get("radio-stacked")
                lists.education = int(questionpoint)
        if currentquestion == 8:
            if request.form.get("radio-stacked") != None:
                questionpoint = request.form.get("radio-stacked")
                lists.wealth = int(questionpoint)
                lists.result = (lists.wealth+lists.education)/2
                print(lists.wealth,lists.education,lists.access,lists.country)
                result = lists.result
                return render_template("result.html",result = result)


        return render_template("quiz.html",questions=questions, count=currentquestion, answer = answer)

    else:
        lists.currentquestion = -1
        lists.country = 0
        lists.education = 0
        lists.wealth = 0
        lists.access = 0
        lists.result = 0
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

@app.route("/result",methods=["GET", "POST"])
def result():
    if request.form.get("interm") != None:
        resultcheck = request.form.get("interm")
        if resultcheck == "wealth":
            return render_template("detailedfinance.html", wealth = lists.wealth)
        if resultcheck == "access":
            return render_template("detailedaccess.html", access = lists.access)
        if resultcheck == "education":
            return render_template("detailededucation.html", education = lists.education)
        if resultcheck == "country":
            return render_template("detailedcountry.html", country = lists.country)
    """Display the quiz"""
    return render_template("detailed.html",access = lists.access, wealth = lists.wealth, education = lists.education, country = lists.country)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
