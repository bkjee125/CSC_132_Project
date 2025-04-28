# Name: Cheyenne Deloney
# Date: 4/23/25
# Description: Heater Buddie Flask Server

from flask import Flask, jsonify, request,  render_template
from datetime import datetime
from zoneinfo import ZoneInfo
from flask_sqlalchemy import SQLAlchemy
import json
import serial, threading, time


app = Flask(__name__, static_folder="static", template_folder="templates")
ser = serial.Serial("COM4", 9600, timeout=1)

latest_temp = None

def read_serial():
    global latest_temp
    while True:
        line = ser.readline().decode("utf-8").strip()
        try:
            latest_temp = float(line)
        except:
            pass
        time.sleep(0.1)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///heater.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
 
class Heater(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # To store the user's desired target temperature.
    _target_temp = db.Column(db.Text, nullable=True)
    # The current temperature reading (sensor connected yet??)
    current_temperature = db.Column(db.Float, default=0)
    # The heater status can be "on" or "off"
    status = db.Column(db.String(10), default="off")
    created_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("UTC")))
    updated_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("UTC")), onupdate=datetime.now(ZoneInfo("UTC")))
    
    @property
    def target_temperature(self):
        """When retrieving target_temperature, decode the JSON string to a float."""
        return float(json.loads(self._target_temp)) if self._target_temp else None

    @target_temperature.setter
    def target_temperature(self, temp):
        """When setting target_temperature, convert the value into a JSON string for storage."""
        self._target_temp = json.dumps(temp)
    
    def to_dict(self):
        """Convert the heater model instance into a dictionary for JSON responses."""
        return {
            "id": self.id,
            "target_temperature": self.target_temperature,
            "current_temperature": self.current_temperature,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Heater {self.id}>"
    
    def __str__(self):
        return (f"Heater {self.id}:\n"
                f"Target Temperature: {self.target_temperature}\n"
                f"Current Temperature: {self.current_temperature}\n"
                f"Status: {self.status}")

 
# Create all the database tables 
 
with app.app_context():
    db.create_all()

 
# Initialize a new session
 
@app.route("/init", methods=["POST"])
def init_heater():
    """
    Initialize a new session.
    Expected JSON body (all keys optional):
    {
        "target_temperature": float,  # defaults to 0°F 
        "status": "on" or "off"         # defaults to "off"
    }
    """
    data = request.get_json() or {}
    target_temp = data.get("target_temperature", 0)
    status = data.get("status", "off")
    
    heater = Heater()
    heater.target_temperature = target_temp
    heater.status = status
    
    db.session.add(heater)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Session initialized.",
        "heater": heater.to_dict()
    })

 
# List all sessions
 
@app.route("/list", methods=["GET"])
def list_heaters():
    """Return a list of all sessions."""
    heaters = Heater.query.all()
    heaters_data = [heater.to_dict() for heater in heaters]
    return jsonify(heaters_data)

 
# Delete a session
 
@app.route("/delete", methods=["POST"])
def delete_heater():
    """
    Delete a session.
    Expected JSON body:
    {
        "id": int
    }
    """
    heater_id = request.json.get("id")
    if heater_id is None:
        return jsonify({
            "success": False,
            "message": "Heater id not provided."
        }), 400
    
    heater = Heater.query.get(heater_id)
    if heater is None:
        return jsonify({
            "success": False,
            "message": "Session not found."
        }), 404
    
    db.session.delete(heater)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": f"Session {heater_id} deleted."
    })

 
# Update settings (target temperature and/or status)
 
@app.route("/set", methods=["POST"])
def set_heater():
    """
    Update the heater settings.
    Expected JSON body:
    {
        "id": int,
        "target_temperature": float (optional),
        "status": "on" or "off" (optional)
    }
    """
    data = request.get_json() or {}
    heater_id = data.get("id")
    if heater_id is None:
        return jsonify({
            "success": False,
            "message": "Heater id not provided."
        }), 400
    
    heater = Heater.query.get(heater_id)
    if heater is None:
        return jsonify({
            "success": False,
            "message": "Session not found."
        }), 404
    
    if "target_temperature" in data:
        heater.target_temperature = data["target_temperature"]
    
    if "status" in data:
        heater.status = data["status"]
    
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Heater settings updated.",
        "heater": heater.to_dict()
    })

 
# Retrieve the current status of a session
 
@app.route("/status", methods=["GET"])
def heater_status():
    """
    Get the current status of a session.
    Expected URL parameter:
      id (the session id)
    Example: /status?id=1
    """
    heater_id = request.args.get("id")
    if not heater_id:
        return jsonify({
            "success": False,
            "message": "Heater id is required."
        }), 400
    
    heater = Heater.query.get(heater_id)
    if heater is None:
        return jsonify({
            "success": False,
            "message": "Session not found."
        }), 404
    
    return jsonify({
        "success": True,
        "heater": heater.to_dict()
    })

# Links backend to webpage.

@app.route("/")
def home():
    return render_template("index.html")
 
# Update the current temperature reading (Is the sensor connected??)
 
@app.route("/update_current", methods=["POST"])
def update_current_temperature():
    """
    Update the current temperature reading.
    Expected JSON body:
    {
        "id": int,
        "current_temperature": float
    }
    """
    data = request.get_json() or {}
    heater_id = data.get("id")
    if heater_id is None:
        return jsonify({
            "success": False,
            "message": "Heater id not provided."
        }), 400
    
    heater = Heater.query.get(heater_id)
    if heater is None:
        return jsonify({
            "success": False,
            "message": "Session not found."
        }), 404
    
    current_temp = data.get("current_temperature")
    if current_temp is None:
        return jsonify({
            "success": False,
            "message": "Current temperature value must be provided."
        }), 400
    
    heater.current_temperature = current_temp
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Current temperature updated.",
        "heater": heater.to_dict()
    })

@app.route("/")
def index():
    return render_template("index.html")

# Start background thread
threading.Thread(target=read_serial, daemon=True).start()

@app.route("/api/temperature")
def api_temp():
    if latest_temp is None:
        return jsonify({"temperature": None}), 204
    return jsonify({"temperature": round(latest_temp, 1)})



 
# Run the Flask server
 
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="8000", use_reloader=False)