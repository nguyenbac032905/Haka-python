
from flask import Flask
from routes.indexRoute import registerRoutes
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Press the green button in the gutter to run the script.
registerRoutes(app)
if __name__ == "__main__":
    app.run(port=5001, debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
