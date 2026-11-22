"""SuperKart sales forecasting REST API (Flask)."""
import joblib
import pandas as pd
from flask import Flask, request, jsonify

# Initialize the Flask application
superkart_api = Flask("SuperKart Sales Predictor")

# Load the serialized pipeline (preprocessing + tuned model) once at start-up
model = joblib.load("superkart_model.joblib")

# Features the model expects, in the order used during training
NUMERIC_FEATURES = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]
CATEGORICAL_FEATURES = ["Product_Sugar_Content", "Store_Size", "Store_Location_City_Type",
                        "Store_Type", "Product_Id_char", "Product_Type_Category"]
MODEL_FEATURES = ["Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
                  "Store_Size", "Store_Location_City_Type", "Store_Type", "Product_Id_char",
                  "Store_Age_Years", "Product_Type_Category"]


def prepare(frame):
    """Validate columns/types and return the frame the model expects (raises ValueError on bad input)."""
    missing = [col for col in MODEL_FEATURES if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing required feature(s): {missing}")
    frame = frame[MODEL_FEATURES].copy()
    for col in NUMERIC_FEATURES:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    bad = [col for col in NUMERIC_FEATURES if frame[col].isna().any()]
    if bad:
        raise ValueError(f"Non-numeric or empty values in: {bad}")
    for col in CATEGORICAL_FEATURES:
        frame[col] = frame[col].astype(str).str.strip()
    return frame


@superkart_api.get("/")
def home():
    """Welcome route."""
    return "Welcome to the SuperKart Sales Forecasting API!"


@superkart_api.get("/health")
def health():
    """Liveness check used to confirm the container is up."""
    return jsonify({"status": "ok"})


@superkart_api.post("/v1/predict")
def predict_sales():
    """Predict sales for a single product-store combination sent as a JSON object."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object with the model features."}), 400
    try:
        input_data = prepare(pd.DataFrame([payload]))
    except ValueError as err:
        return jsonify({"error": str(err)}), 400

    prediction = float(model.predict(input_data)[0])
    return jsonify({"Predicted_Sales": round(prediction, 2)})


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """Predict sales for every row of an uploaded CSV file (form field 'file')."""
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV file in the form field 'file'."}), 400
    try:
        raw = pd.read_csv(request.files["file"])
    except Exception:
        return jsonify({"error": "Could not read the uploaded file as CSV."}), 400
    if raw.empty:
        return jsonify({"error": "The uploaded CSV has no rows."}), 400
    try:
        input_data = prepare(raw)
    except ValueError as err:
        return jsonify({"error": str(err)}), 400

    predictions = model.predict(input_data)
    # Row index -> predicted sales
    return jsonify({str(idx): round(float(pred), 2) for idx, pred in zip(raw.index, predictions)})


@superkart_api.errorhandler(Exception)
def handle_unexpected(err):
    """Return JSON instead of an HTML stack trace for unexpected errors."""
    code = getattr(err, "code", 500)
    return jsonify({"error": str(err)}), code if isinstance(code, int) else 500


# Run the Flask app in debug mode when executed directly (Gunicorn is used inside Docker)
if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=True)
