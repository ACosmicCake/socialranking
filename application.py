import os
import json
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology,convert,people
from lists import questions,answer


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
with open('countries.json') as f:
    countries = json.load(f)

with open('income_levels.json') as f:
    income_levels = json.load(f)

highincome = [country for country, data in income_levels.items() if data['incomeLevel'] == 'High income']
uppermiddleincome = [country for country, data in income_levels.items() if data['incomeLevel'] == 'Upper middle income']
lowmiddleincome = [country for country, data in income_levels.items() if data['incomeLevel'] == 'Lower middle income']
lowincome = [country for country, data in income_levels.items() if data['incomeLevel'] == 'Low income']


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


def calculate_score(country, access, education, wealth):
    """
    Calculates the final socioeconomic status (SES) score based on the user's answers.

    The score is calculated using a weighted average of the following four components:
    - Country: Based on the income level of the user's country of residence.
    - Access: Reflects the user's access to essential services like clean water, electricity, and healthcare.
    - Education: Based on the user's level of educational attainment.
    - Wealth: Reflects the user's daily income and financial stability.

    Each component is assigned a weight based on its relative importance in determining SES.
    """
    # Weights for each category, based on the following justification:
    # - Wealth and Education are given the highest weights as they are the most significant predictors of socioeconomic status.
    # - Occupation is also a strong predictor, but it is often correlated with education and income, so it is given a slightly lower weight.
    # - Access to basic services is a fundamental component of well-being, but it is often a consequence of wealth and education, so it is given a lower weight.
    # - Social capital and intergenerational mobility are also important factors, but they are more difficult to measure and are given a lower weight in this model.
    weights = {
        'wealth': 0.30,
        'education': 0.30,
        'occupation': 0.20,
        'access': 0.10,
        'social_capital': 0.05,
        'intergenerational_mobility': 0.05
    }

    # Calculate the weighted score
    score = (session.get('wealth', 0) * weights['wealth']) + \
            (session.get('education', 0) * weights['education']) + \
            (session.get('occupation', 0) * weights['occupation']) + \
            (session.get('access', 0) * weights['access']) + \
            (session.get('social_capital', 0) * weights['social_capital']) + \
            (session.get('intergenerational_mobility', 0) * weights['intergenerational_mobility'])
    return score

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        currentquestion = session.get('currentquestion', -1) + 1
        session['currentquestion'] = currentquestion

        country = request.form.get("country")
        if country:
            if country in highincome:
                session['country'] = 16
            elif country in uppermiddleincome:
                session['country'] = 51
            elif country in lowmiddleincome:
                session['country'] = 91
            elif country in lowincome:
                session['country'] = 100

        question_category = questions[currentquestion -1]['category']
        question_point = request.form.get("radio-stacked")

        if question_point:
            if question_category not in session:
                session[question_category] = 0
            session[question_category] += int(question_point)

        if currentquestion == len(questions):
            # Calculate the average score for each category
            for category in set(q['category'] for q in questions):
                if category in session:
                    session[category] = session[category] / len([q for q in questions if q['category'] == category])
            session['result'] = calculate_score(
                session.get('country', 0),
                session.get('access', 0),
                session.get('education', 0),
                session.get('wealth', 0)
            )
            return render_template("result.html", result=session['result'])

        return render_template("quiz.html", questions=questions, count=currentquestion, answer=answer)

    else:
        session.clear()
        session['currentquestion'] = -1
        return render_template("quizcountry.html", countries=countries)



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

@app.route("/learn")
def learn():
    """Display the learn more page"""

    return render_template("learn.html",)

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
