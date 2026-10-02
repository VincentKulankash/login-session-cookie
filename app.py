#In charge of flask routes, session logic, cookie handling
from flask import (
    Flask,
    session,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    make_response
)

from werkzeug.security import generate_password_hash, check_password_hash

import db 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('login.html')

if __name__ == ('__main__'):
    app.run(debug=True, port=5001)
    
     