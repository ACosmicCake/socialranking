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
        
        
        # get the GNI capita of the users country
        country = request.form.get("country")
        if country in highincome:
            session['country'] = 16
        if country in uppermiddleincome:
            session['country'] = 51
        if country in lowmiddleincome:
            session['country'] = 91
        if country in lowincome:
            session['country'] = 100
            
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
                session['result'] = (session['wealth']+session['education'])/2
                print(session['wealth'],session['education'],session['access'],session['country'])
                result = session['result']
                return render_template("result.html",result = result)
        
        
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
    
@app.route("/result",methods=["GET", "POST"])
def result():
    if request.form.get("interm") != None:
        resultcheck = request.form.get("interm")
        if resultcheck == "wealth":
            return render_template("detailedfinance.html", wealth = session['wealth'])
        if resultcheck == "access":
            return render_template("detailedaccess.html", access = session['access'])
        if resultcheck == "education":
            return render_template("detailededucation.html", education = session['education'])
        if resultcheck == "country":
            return render_template("detailedcountry.html", country = session['country'])
    """Display the quiz"""
    return render_template("detailed.html",access = session['access'], wealth = session['wealth'], education = session['education'], country = session['country'])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
