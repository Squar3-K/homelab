from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from sklearn.ensemble import IsolationForest
from prometheus_client import Counter, Histogram, generate_latest
import numpy as np
import time
import json
import redis
import logging
import os

app = FastAPI()

# Redis connection
try:
    r = redis.Redis(
        host='redis',
        port=6379,
        password=os.environ.get('REDIS_PASSWORD'),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    r.ping()
    logging.info("Redis connected successfully")
except Exception as e:
    logging.error(f"Redis connection failed: {e}")
    r = None

model = IsolationForest(contamination=0.15, random_state=42)
is_trained = False
training_data = []
endpoint_stats = {}

REQUEST_COUNT = Counter('api_requests_total', 'Total requests', ['endpoint', 'status'])
RESPONSE_TIME = Histogram('api_response_seconds', 'Response time', ['endpoint'])
ANOMALY_COUNT = Counter('api_anomalies_total', 'Anomalies detected', ['endpoint'])

def extract_features(log: dict) -> list:
    status = int(log.get('status_code', 200))
    response_time = float(log.get('response_time', 0))
    payload_size = int(log.get('payload_size', 0))
    hour = int(log.get('hour_of_day', 0))
    is_error = 1 if status >= 400 else 0
    return [
        response_time * 1000,
        is_error * 10,
        float(status),
        float(payload_size) / 100,
        float(hour),
    ]

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "trained": is_trained,
        "samples": len(training_data)
    }

@app.get("/stats")
async def stats():
    total = len(training_data)
    anomaly_count = int(ANOMALY_COUNT.labels(endpoint='unknown')._value.get()) if is_trained else 0
    return {
        "total_requests": total,
        "trained": is_trained,
        "samples": total,
        "endpoint_stats": endpoint_stats
    }

@app.post("/log")
async def log_request(request: Request):
    global is_trained, training_data, endpoint_stats

    try:
        body = await request.json()
    except Exception:
        return {"anomaly": False, "trained": is_trained}

    try:
        features = extract_features(body)
        training_data.append(features)

        # Train after 100 samples
        if len(training_data) >= 100 and len(training_data) % 10 == 0:
            model.fit(training_data[-1000:])
            is_trained = True

        # Detect anomaly
        is_anomaly = False
        score = 0.0
        if is_trained:
            score = float(model.decision_function([features])[0])
            is_anomaly = bool(model.predict([features])[0] == -1)
            if is_anomaly:
                ANOMALY_COUNT.labels(
                    endpoint=str(body.get('endpoint', 'unknown'))
                ).inc()

        # Update endpoint stats
        ep = str(body.get('endpoint', 'unknown'))
        if ep not in endpoint_stats:
            endpoint_stats[ep] = {'total': 0, 'errors': 0, 'anomalies': 0}
        endpoint_stats[ep]['total'] += 1
        if int(body.get('status_code', 200)) >= 400:
            endpoint_stats[ep]['errors'] += 1
        if is_anomaly:
            endpoint_stats[ep]['anomalies'] += 1

        # Prometheus metrics
        REQUEST_COUNT.labels(
            endpoint=ep,
            status=str(body.get('status_code', 200))
        ).inc()
        RESPONSE_TIME.labels(endpoint=ep).observe(
            float(body.get('response_time', 0))
        )

        # Store in Redis safely
        if r:
            log_entry = {
                'endpoint': ep,
                'status_code': int(body.get('status_code', 200)),
                'response_time': float(body.get('response_time', 0)),
                'anomaly': is_anomaly,
                'score': score
            }
            r.lpush('api_logs', json.dumps(log_entry))
            r.ltrim('api_logs', 0, 9999)

        return {
            "anomaly": is_anomaly,
            "trained": is_trained,
            "score": score
        }

    except Exception as e:
        logging.error(f"Error processing log: {e}")
        return {"anomaly": False, "trained": is_trained, "error": str(e)}

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())

@app.get("/logs/recent")
async def recent_logs():
    if not r:
        return []
    try:
        logs = r.lrange('api_logs', 0, 99)
        return [json.loads(l) for l in logs]
    except Exception as e:
        return {"error": str(e)}
