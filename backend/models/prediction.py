from datetime import datetime

from backend.extensions import db


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    property_type = db.Column(db.String(50))
    city = db.Column(db.String(100))
    locality = db.Column(db.String(200))
    area_sqft = db.Column(db.Float)
    bhk = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    predicted_price = db.Column(db.Float)
    lower_bound = db.Column(db.Float)
    upper_bound = db.Column(db.Float)
    reliability = db.Column(db.String(20))
    recommendation = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    property_data = db.Column(db.Text)


__all__ = ["Prediction"]
