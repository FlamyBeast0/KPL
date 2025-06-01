# app.py - This is your Receiving App's code with Firestore integration

from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import random
import firebase_admin
from firebase_admin import credentials, firestore
import os # Import os module to handle environment variables

app = Flask(__name__)
# Enable CORS for your app, allowing all origins for initial deployment.
# IMPORTANT: For production, replace "*" with your specific Firebase Hosting domain (e.g., "https://your-project-id.web.app")
CORS(app, resources={r"/*": {"origins": "*"}}) #

# --- Firebase Initialization ---
# The 'firebase_credentials.json' file must be in the same directory as app.py
try:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully!")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    print("Please ensure 'firebase_credentials.json' is in the same directory and is valid.")
    # In a production app, you might want to exit or log this more robustly.

# This is the 'listening' part. It listens for messages sent to '/receive-order'
@app.route('/receive-order', methods=['POST'])
def handle_order_request():
    print("Someone sent a message to my Receiving App!")

    try:
        order_data = request.get_json()
        if not order_data:
            return jsonify({"success": False, "message": "No data received or data is not JSON."}), 400
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return jsonify({"success": False, "message": "Invalid JSON format."}), 400

    patient_name = order_data.get('patientName', 'N/A')
    phone_number = order_data.get('phoneNumber', 'N/A')
    email_address = order_data.get('emailAddress', 'N/A')
    selected_tests = order_data.get('tests', [])

    print(f"--- Received Order Details ---")
    print(f"Patient Name: {patient_name}")
    print(f"Phone Number: {phone_number}")
    print(f"Email: {email_address}")
    print(f"Selected Tests:")
    for test in selected_tests:
        print(f"  - {test.get('name')} (ID: {test.get('id')}, Price: {test.get('price')})")
    print(f"----------------------------")

    # Your Receiving App creates the official serial number
    today = datetime.date.today()
    serial_prefix = "KPL-" + today.strftime("%y%m%d") # e.g., KPL-250531
    random_suffix = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=6)) # 6 random chars
    official_serial_number = f"{serial_prefix}-{random_suffix}"

    print(f"Generated Official Serial Number: {official_serial_number}")

    # --- SAVE ORDER TO FIRESTORE ---
    try:
        # Create a new document in the 'orders' collection with the serial number as its ID
        order_ref = db.collection('orders').document(official_serial_number)
        order_data_to_save = {
            "serialNumber": official_serial_number,
            "patientName": patient_name,
            "phoneNumber": phone_number,
            "emailAddress": email_address,
            "tests": selected_tests, # Save the list of test objects
            "orderDate": firestore.SERVER_TIMESTAMP # Automatically adds server timestamp
        }
        order_ref.set(order_data_to_save)
        print(f"Order {official_serial_number} saved to Firestore.")
    except Exception as e:
        print(f"Error saving order to Firestore: {e}")
        # Log the error, but for now we'll allow the response to proceed.

    # Send a success message back to your website, including the official serial number
    return jsonify({
        "success": True,
        "message": "Order received successfully by Receiving App!",
        "serialNumber": official_serial_number, # Send the official serial number back
        "patientName": patient_name, # Also send patient name for confirmation display
        "selected_tests": selected_tests # Also send tests for confirmation display
    }), 200

# New endpoint to get order details by serial number from Firestore
@app.route('/get-order-status', methods=['POST'])
def get_order_status():
    try:
        request_data = request.get_json()
        serial_number = request_data.get('serialNumber')

        if not serial_number:
            return jsonify({"status": "error", "message": "Serial number is required."}), 400

        print(f"Attempting to retrieve order: {serial_number}")
        order_ref = db.collection('orders').document(serial_number)
        order_doc = order_ref.get()

        if order_doc.exists:
            order_details = order_doc.to_dict()
            print(f"Order {serial_number} found in Firestore.")
            # Convert Firestore timestamp to a readable string if needed by frontend
            if 'orderDate' in order_details and hasattr(order_details['orderDate'], 'strftime'):
                order_details['orderDate'] = order_details['orderDate'].strftime("%Y-%m-%d %H:%M:%S")
            return jsonify({"status": "success", "order": order_details}), 200
        else:
            print(f"Order {serial_number} not found in Firestore.")
            return jsonify({"status": "error", "message": "Order not found."}), 404
    except Exception as e:
        print(f"Error retrieving order from Firestore: {e}")
        return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500

# Placeholder for AI Interpretation and Health Tips (frontend now calls Gemini directly)
@app.route('/interpret-report', methods=['POST'])
def interpret_report():
    if request.is_json:
        data = request.get_json()
        report_text = data.get('report_text', '')
        print(f"Received report text for interpretation (backend mock): {report_text}")
        mock_interpretation = f"Backend Mock Interpretation for '{report_text}': This response came from your Python backend. Frontend now calls Gemini directly for AI features."
        return jsonify({"status": "success", "interpretation": mock_interpretation}), 200
    return jsonify({"status": "error", "message": "Invalid request"}), 400

@app.route('/generate-health-tips', methods=['POST'])
def generate_health_tips():
    if request.is_json:
        data = request.get_json()
        health_goal = data.get('health_goal', '')
        print(f"Received health goal for tips (backend mock): {health_goal}")
        mock_tips = f"Backend Mock Health Tips for '{health_goal}': This response came from your Python backend. Frontend now calls Gemini directly for AI features."
        return jsonify({"status": "success", "tips": mock_tips}), 200
    return jsonify({"status": "error", "message": "Invalid request"}), 400

# IMPORTANT: This block should be commented out or removed for Cloud Run/Render deployment.
# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

