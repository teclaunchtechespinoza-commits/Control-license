# 🚀 License Manager - Deployment Guide v1.3.0

## 📋 Deployment Overview

Este guia fornece instruções completas para deployment do **License Manager v1.3.0** em diferentes ambientes, desde desenvolvimento local até produção enterprise.

---

## 🏗️ Arquitetura de Deploy

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Architecture                   │
├─────────────────────────────────────────────────────────────┤
│  Load Balancer (nginx/HAProxy)                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)     │  Backend (FastAPI)                │
│  - Nginx static      │  - Gunicorn/Uvicorn              │  
│  - Build optimized   │  - Multiple workers               │
│  - CDN integration   │  - Auto-scaling                   │
├─────────────────────────────────────────────────────────────┤
│  Job Scheduler (APScheduler)                              │
│  - Persistent jobs   │  - Health monitoring              │
│  - Auto-recovery     │  - Performance tracking           │
├─────────────────────────────────────────────────────────────┤
│  Database Cluster (MongoDB)                               │
│  - Replica Set       │  - Optimized Indexes              │
│  - Auto-failover     │  - Performance monitoring         │
├─────────────────────────────────────────────────────────────┤
│  Monitoring & Logging                                     │
│  - Structured logs   │  - Performance metrics            │
│  - Error tracking    │  - Security monitoring            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Pré-requisitos

### **Sistema Operacional**
- Ubuntu 20.04+ / CentOS 8+ / Docker
- 4GB+ RAM disponível
- 20GB+ espaço em disco
- CPU com 2+ cores

### **Software Dependencies**
```bash
# Base requirements
- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+ & Yarn
- Python 3.11+
- MongoDB 7.0+

# Optional (production)
- Nginx 1.18+
- SSL certificates
- Domain name configured
```

### **Network Requirements**
```
Ports Required:
├── 3000 - Frontend (development)
├── 8001 - Backend API
├── 27017 - MongoDB  
├── 80/443 - HTTP/HTTPS (production)
└── 22 - SSH (deployment)

Outbound Access:
├── NPM registry (npmjs.org)
├── Python PyPI (pypi.org)  
├── MongoDB Atlas (if using)
└── WhatsApp Business API
```

---

## 🔧 Environment Configuration

### **1. Environment Variables**

**Backend (.env)**
```bash
# Database
MONGO_URL=mongodb://localhost:27017/
DB_NAME=license_manager

# Security  
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# WhatsApp Integration
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_ACCESS_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id

# Notification Settings
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=noreply@yourcompany.com
EMAIL_PASSWORD=your-email-password

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
CACHE_TIMEOUT=300
```

**Frontend (.env)**
```bash
# API Configuration
REACT_APP_BACKEND_URL=https://api.yourcompany.com/api
REACT_APP_ENVIRONMENT=production

# Features
REACT_APP_WHATSAPP_ENABLED=true
REACT_APP_MULTI_TENANT_ENABLED=true
REACT_APP_ANALYTICS_ENABLED=true

# Performance
GENERATE_SOURCEMAP=false
BUILD_PATH=build
```

### **2. Security Configuration**
```bash
# Generate secure JWT secret
openssl rand -hex 32

# Create application user (Linux)
sudo adduser --system --group licensemanager
sudo usermod -aG docker licensemanager

# Set file permissions
chmod 600 .env
chmod 755 /app
chown -R licensemanager:licensemanager /app
```

---

## 📦 Deployment Methods

## **Method 1: Docker Compose (Recommended)**

### **docker-compose.yml**
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - ./mongodb-init:/docker-entrypoint-initdb.d
    ports:
      - "27017:27017"
    networks:
      - license_manager_network

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - MONGO_URL=mongodb://root:${MONGO_ROOT_PASSWORD}@mongodb:27017/
      - DB_NAME=license_manager
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "8001:8001"
    depends_on:
      - mongodb
    networks:
      - license_manager_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - license_manager_network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - frontend
      - backend
    networks:
      - license_manager_network

volumes:
  mongodb_data:
    driver: local
    
networks:
  license_manager_network:
    driver: bridge
```

### **Backend Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/api/health || exit 1

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### **Frontend Dockerfile**
```dockerfile
# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy source code and build
COPY . .
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN yarn build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### **Deployment Commands**
```bash
# Clone repository
git clone <repository-url>
cd license-manager

# Create environment file
cp .env.example .env
# Edit .env with your configurations

# Build and deploy
docker-compose build
docker-compose up -d

# Verify deployment  
docker-compose ps
docker-compose logs -f

# Access application
curl http://localhost/api/health
```

---

## **Method 2: Manual Deployment**

### **Backend Deployment**
```bash
# 1. Setup Python environment
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Database setup
# Ensure MongoDB is running with optimized configuration
python3 database_optimizer.py

# 3. Run with Gunicorn (production)
gunicorn server:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8001 \
  --timeout 60 \
  --keep-alive 2 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### **Frontend Deployment**
```bash
# 1. Build production bundle
cd frontend
yarn install --frozen-lockfile
yarn build

# 2. Setup Nginx
sudo cp build/* /var/www/html/
sudo systemctl reload nginx

# 3. Configure Nginx
sudo nano /etc/nginx/sites-available/license-manager
```

**Nginx Configuration**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

---

## **Method 3: Kubernetes Deployment**

### **Kubernetes Manifests**

**namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: license-manager
```

**mongodb-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb
  namespace: license-manager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: "root"
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: password
        volumeMounts:
        - name: mongodb-storage
          mountPath: /data/db
      volumes:
      - name: mongodb-storage
        persistentVolumeClaim:
          claimName: mongodb-pvc
```

**backend-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: license-manager
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: license-manager-backend:1.3.0
        ports:
        - containerPort: 8001
        env:
        - name: MONGO_URL
          valueFrom:
            secretKeyRef:
              name: backend-secret
              key: mongo-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: backend-secret
              key: jwt-secret
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

### **Deploy to Kubernetes**
```bash
# Apply manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n license-manager
kubectl get services -n license-manager

# Port forward for testing
kubectl port-forward -n license-manager service/backend 8001:8001
```

---

## 🔍 Monitoring & Health Checks

### **Health Check Endpoints**
```bash
# Application health
curl http://localhost:8001/api/health

# Database connectivity
curl http://localhost:8001/api/stats

# Job scheduler status  
curl http://localhost:8001/api/scheduler/status

# Structured logging analytics
curl http://localhost:8001/api/logs/analytics
```

### **Performance Monitoring**
```bash
# MongoDB performance
mongo --eval "db.runCommand({serverStatus: 1})"

# System resources
htop
iotop
netstat -tuln

# Application metrics
curl http://localhost:8001/api/logs/analytics | jq '.performance_metrics'
```

### **Log Monitoring**
```bash
# Structured logs
tail -f /app/structured_logs.json | jq '.'

# Audit logs
tail -f /app/audit_logs.json | jq '.'

# Application logs
tail -f /app/maintenance_log.txt

# System logs
journalctl -u license-manager -f
```

---

## 🔒 Security Hardening

### **Application Security**
```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp  
sudo ufw allow 443/tcp
sudo ufw deny 27017/tcp  # Block direct DB access

# 3. SSL/TLS configuration
certbot --nginx -d yourdomain.com

# 4. Secure file permissions
chmod 600 .env
chmod 700 /app/logs
chown -R licensemanager:licensemanager /app
```

### **MongoDB Security**
```javascript
// Enable authentication
use admin
db.createUser({
  user: "admin",
  pwd: "secure_password", 
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase"]
});

// Enable security in mongod.conf
security:
  authorization: enabled
```

### **Network Security**
```bash
# Rate limiting (nginx)
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;

# Fail2ban configuration
sudo apt install fail2ban
sudo systemctl enable fail2ban

# DDoS protection
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

---

## 📊 Performance Optimization

### **Database Optimization**
```bash
# 1. Run database optimizer (automated in v1.3.0)
python database_optimizer.py

# 2. MongoDB configuration (mongod.conf)
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

# 3. Connection pooling
net:
  maxIncomingConnections: 1000
  connectionOptions:
    maxPoolSize: 100
```

### **Application Tuning**
```bash
# 1. Backend workers (Gunicorn)
workers = (2 * CPU_cores) + 1
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = 1000
max_requests_jitter = 100

# 2. Frontend optimization (nginx)
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;

# 3. Caching strategy
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 🔄 Backup & Recovery

### **Automated Backup Script**
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/license-manager"
DB_NAME="license_manager"

# Create backup directory
mkdir -p $BACKUP_DIR

# MongoDB backup
mongodump --db $DB_NAME --out $BACKUP_DIR/mongodb_$DATE

# Application files backup
tar -czf $BACKUP_DIR/app_files_$DATE.tar.gz /app --exclude=/app/logs

# Structured logs backup
cp /app/structured_logs.json $BACKUP_DIR/logs_$DATE.json
cp /app/audit_logs.json $BACKUP_DIR/audit_$DATE.json

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "mongodb_*" -mtime +7 -delete
find $BACKUP_DIR -name "app_files_*" -mtime +7 -delete
find $BACKUP_DIR -name "*_logs_*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### **Recovery Procedure**
```bash
# 1. Stop application
docker-compose down
# or
sudo systemctl stop license-manager

# 2. Restore database
mongorestore --db license_manager /path/to/backup/mongodb_YYYYMMDD_HHMMSS/

# 3. Restore application files
tar -xzf /path/to/backup/app_files_YYYYMMDD_HHMMSS.tar.gz -C /

# 4. Restart application
docker-compose up -d
# or  
sudo systemctl start license-manager

# 5. Verify recovery
curl http://localhost:8001/api/health
```

---

## 🚨 Troubleshooting

### **Common Issues**

**Backend Won't Start**
```bash
# Check logs
tail -f /var/log/supervisor/backend.err.log

# Common fixes
pip install -r requirements.txt  # Missing dependencies
python database_optimizer.py     # Database not optimized
chmod +x server.py              # Permission issues
```

**Database Connection Issues**  
```bash
# Test connectivity
mongo --eval "db.adminCommand('ismaster')"

# Check MongoDB status
sudo systemctl status mongod

# Verify network
netstat -tuln | grep 27017
```

**Frontend Build Issues**
```bash
# Clear cache and rebuild
rm -rf node_modules build
yarn install
yarn build

# Check environment variables
env | grep REACT_APP
```

**Performance Issues**
```bash
# Check system resources
htop
iotop
df -h

# Check database performance  
mongo --eval "db.licenses.explain().find({tenant_id: 'default'})"

# Check application metrics
curl http://localhost:8001/api/logs/analytics
```

### **Performance Monitoring Commands**
```bash
# Real-time system monitoring
watch -n 1 'free -m && df -h && netstat -tuln'

# Application performance
curl -s http://localhost:8001/api/scheduler/status | jq '.statistics'

# Database performance
mongostat --host localhost:27017 -u admin -p password

# Log analytics
tail -f /app/structured_logs.json | jq 'select(.details.duration_ms > 1000)'
```

---

## ✅ Post-Deployment Checklist

### **Immediate Verification (15 minutes)**
- [ ] Health endpoints responding (`/api/health`, `/ping`)
- [ ] Authentication working (login with test user)
- [ ] Database connectivity confirmed (`/api/stats`)
- [ ] Job scheduler running (`/api/scheduler/status`)
- [ ] Structured logging active (`/api/logs/analytics`)
- [ ] SSL certificate valid (production)

### **Functional Testing (30 minutes)**
- [ ] User registration/login flow
- [ ] License CRUD operations
- [ ] Client management (PF/PJ)
- [ ] Notification system working
- [ ] Multi-tenant isolation verified
- [ ] RBAC permissions enforced

### **Performance Verification (15 minutes)**
- [ ] API response times < 100ms average
- [ ] Database queries using indexes
- [ ] No memory leaks detected
- [ ] CPU usage < 70% under load
- [ ] Disk space sufficient (>20% free)

### **Security Verification (20 minutes)**
- [ ] HTTPS enforced (production)
- [ ] JWT tokens expiring correctly
- [ ] Sensitive data masked in logs
- [ ] Rate limiting active
- [ ] Firewall configured properly
- [ ] Audit logging working

### **Monitoring Setup (10 minutes)**
- [ ] Log rotation configured
- [ ] Backup schedule active
- [ ] Alerting rules configured
- [ ] Performance monitoring active
- [ ] Error tracking enabled

---

## 📞 Support & Maintenance

### **Support Channels**
- 📧 **Technical Support**: tech-support@licensemanager.com
- 🎫 **Bug Reports**: GitHub Issues
- 📚 **Documentation**: `/docs` endpoint
- 💬 **Community**: Discord/Slack

### **Maintenance Windows**
- **Regular Updates**: Monthly (first Sunday, 2-4 AM)
- **Security Patches**: As needed (within 48h)
- **Database Maintenance**: Quarterly
- **Performance Reviews**: Monthly

### **Emergency Procedures**
1. **System Down**: Contact on-call engineer
2. **Data Breach**: Activate incident response plan
3. **Performance Issues**: Scale resources immediately
4. **Security Alerts**: Follow security playbook

---

**🎉 Deployment Guide v1.3.0 Complete**  
*License Manager is now ready for enterprise production deployment!*

*For additional support: deployment-support@licensemanager.com*