# ML-Powered API Monitoring Homelab

A self-hosted cloud infrastructure running on bare metal + Oracle Cloud,
featuring real-time ML anomaly detection for APIs.

##  Architecture
```
Physical Server (Ubuntu 24.04)     Oracle Cloud (Free Tier)
├── Nextcloud (File Storage)        ├── Backup Storage
├── Vaultwarden (Passwords)         └── Overflow APIs
├── ML Anomaly Detector
├── Prometheus + Grafana + Loki
├── FastAPI (monitored APIs)
└── Cloudflare Tunnel (HTTPS)
```

##  ML Anomaly Detection

- Algorithm: Isolation Forest
- Detects: unusual error rates, response time spikes, traffic anomalies
- Training: continuous rolling window
- Features: response time, status code, payload size, hour of day

## Stack

| Layer | Technology |
|---|---|
| OS | Ubuntu Server 24.04 LTS |
| Containers | Docker + Docker Compose |
| Reverse Proxy | Nginx Proxy Manager |
| File Cloud | Nextcloud |
| Password Manager | Vaultwarden |
| API Framework | FastAPI (Python) |
| ML Library | scikit-learn |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Log Aggregation | Loki |
| Database | PostgreSQL |
| Cache | Redis |
| Tunnel | Cloudflare Tunnel |
| Security | UFW + Fail2ban + SSL |
| Cloud | Oracle Cloud Infrastructure |

## Live Demo

| Service | URL |
|---|---|
| File Cloud | https://cloud.cloudalex.me |
| API | https://api.cloudalex.me/docs |
| Monitoring | https://monitor.cloudalex.me |

## Security

- SSH key authentication only
- UFW firewall 
- Fail2ban 
- Cloudflare Tunnel
- SSL/TLS via Cloudflare

## Services

### Nextcloud
Self-hosted Google Drive alternative with mobile sync,
photo backup, calendar and contacts sync.

### Vaultwarden
Self-hosted Bitwarden-compatible password manager.
Zero-knowledge encryption, accessible from any device.

### ML API Monitoring
Real-time anomaly detection system that:
- Intercepts every API request via FastAPI middleware
- Extracts features (latency, status, payload size)
- Trains Isolation Forest model continuously
- Flags anomalous requests in real time
- Visualizes everything in Grafana dashboards

### Observability Stack
- Prometheus scrapes metrics every 15 seconds
- Loki aggregates logs from all containers
- Grafana dashboards show request rates, anomalies, latency

## Project Structure

\`\`\`
homelab/
├── docker-compose.yml      # Full stack definition
├── .env                    # Secrets (not committed)
├── monitoring/
│   ├── ml_detector/        # ML anomaly detection service
│   │   ├── detector.py     # Isolation Forest model + API
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── prometheus.yml      # Scrape config
│   └── loki-config.yml     # Log aggregation config
└── myapi/                  # Sample monitored FastAPI app
    ├── main.py             # API with monitoring middleware
    ├── Dockerfile
    └── requirements.txt
\`\`\`

## Skills Demonstrated

- Linux system administration
- Docker & container orchestration
- Cloud infrastructure (Oracle Cloud)
- Machine learning engineering (deployment)
- API development (FastAPI)
- Observability & monitoring
- Network security & hardening
- DevOps practices
# homelab
