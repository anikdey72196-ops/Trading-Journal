from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from database import db

import os
from dotenv import load_dotenv

# Import our new Blueprints
from auth_routes import auth_bp
from main_routes import main_bp

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
root_dir = os.path.abspath(os.path.join(base_dir, '..'))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templets'),
            static_folder=os.path.join(base_dir, 'static'),
            instance_path=os.path.join(root_dir, 'instance'))

# Load environment variables from app/.env
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///trading_journal.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_fallback_secret')

csrf = CSRFProtect(app)
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)
