# SuperKart Sales Forecast

Containerized sales-forecasting app: a Flask REST API (`backend/`, port 7860) serving a tuned ML pipeline,
and a Streamlit UI (`frontend/`, port 8501), connected over a Docker bridge network.

## Run in GitHub Codespaces
```bash
cd backend && docker build -t superkart-backend . && cd ..
cd frontend && docker build -t superkart-frontend . && cd ..
docker network create superkart-network
docker run -d --name backend --network superkart-network -p 7860:7860 superkart-backend
docker run -d --name frontend --network superkart-network -p 8501:8501 superkart-frontend
```
Make ports 7860 and 8501 **Public** in the Ports tab, then open the 8501 URL.

## API
- `POST /v1/predict` - JSON with the 10 model features -> `{"Predicted_Sales": ...}`
- `POST /v1/predictbatch` - CSV upload (field `file`) -> `{row_index: predicted_sales}`
