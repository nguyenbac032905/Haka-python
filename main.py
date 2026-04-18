from flask import Flask
from flask_cors import CORS
from routes.indexRoute import registerRoutes

app = Flask(__name__)
CORS(app)

registerRoutes(app)

if __name__ == "__main__":
    app.run(port=3002, debug=True)
