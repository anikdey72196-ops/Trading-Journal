from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE user MODIFY Password VARCHAR(255);"))
        db.session.commit()
        print("SUCCESS! The Password column in the User table has been updated to VARCHAR(255).")
    except Exception as e:
        print(f"Error: {e}")
