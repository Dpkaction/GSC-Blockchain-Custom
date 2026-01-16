#!/bin/bash

# GSC Coin Mainnet Deployment Script
# This script deploys GSC blockchain nodes to cloud infrastructure

set -e

echo "🚀 GSC Coin Mainnet Deployment Script"
echo "======================================"

# Configuration
PROJECT_NAME="gsc-mainnet"
DOCKER_IMAGE="gsccoin/mainnet-node"
VERSION="1.0.0"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t $DOCKER_IMAGE:$VERSION .
docker tag $DOCKER_IMAGE:$VERSION $DOCKER_IMAGE:latest

echo "✅ Docker image built successfully"

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Generate self-signed SSL certificate if not exists
if [ ! -f "ssl/gsccoin.crt" ]; then
    echo "🔐 Generating SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/gsccoin.key \
        -out ssl/gsccoin.crt \
        -subj "/C=US/ST=State/L=City/O=GSC Coin/CN=gsccoin.network"
    echo "✅ SSL certificate generated"
fi

# Create Grafana directories
mkdir -p grafana/dashboards grafana/datasources

# Create Grafana datasource configuration
cat > grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Create basic Grafana dashboard
cat > grafana/dashboards/gsc-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "GSC Blockchain Dashboard",
    "tags": ["gsc", "blockchain"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Blockchain Height",
        "type": "stat",
        "targets": [
          {
            "expr": "gsc_blockchain_height",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Connected Peers",
        "type": "stat",
        "targets": [
          {
            "expr": "gsc_network_peers",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF

# Deploy with Docker Compose
echo "🚀 Deploying GSC Mainnet..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
services=("gsc-seed-1" "gsc-seed-2" "gsc-node" "nginx" "prometheus" "grafana")

for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        docker-compose logs $service
    fi
done

echo ""
echo "🎉 GSC Mainnet Deployment Complete!"
echo "=================================="
echo ""
echo "📊 Access Points:"
echo "• Main API: https://gsccoin.network/api/v1/info"
echo "• Seed Node 1: https://seed1.gsccoin.network/api/v1/info"
echo "• Seed Node 2: https://seed2.gsccoin.network/api/v1/info"
echo "• Grafana Dashboard: http://localhost:3000 (admin/gsc_admin_2026)"
echo "• Prometheus: http://localhost:9093"
echo ""
echo "🔧 Management Commands:"
echo "• View logs: docker-compose logs -f [service-name]"
echo "• Stop all: docker-compose down"
echo "• Restart: docker-compose restart [service-name]"
echo "• Scale nodes: docker-compose up -d --scale gsc-node=3"
echo ""
echo "📝 Next Steps:"
echo "1. Configure your domain DNS to point to this server"
echo "2. Replace self-signed SSL with proper certificates"
echo "3. Set up monitoring alerts"
echo "4. Configure backup procedures"
echo ""
echo "🌐 P2P Network Ports:"
echo "• Seed Node 1: 8333"
echo "• Seed Node 2: 8343"
echo "• Regular Node: 8353"
echo ""
echo "Happy mining! 🎯"
