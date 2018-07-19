from flask import Flask
app = Flask(__name__, static_folder='', static_url_path='')
from app import application
