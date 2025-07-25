import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def convert(value):
    """Format value as USD."""
    return f"{value:,.2f}"
    
    
def people(value):
    """Format value as people"""
    value = 100 - value
    temp = value / 100
    people = temp * 7674000000
    return f"{people:,.0f}"