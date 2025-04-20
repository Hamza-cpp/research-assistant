from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__, static_folder="../static")
    
    # Enable CORS for all routes to allow React app to connect
    CORS(app)
    
    # Load configuration
    app.config.from_pyfile("../config/settings.py", silent=True)
    
    # Import routes - this applies them directly to the app
    from app.api.routes import register_routes
    register_routes(app)
    
    return app