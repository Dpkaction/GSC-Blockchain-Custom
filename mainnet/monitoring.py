"""
GSC Coin Mainnet Monitoring and Health Checks
Production monitoring with Prometheus metrics and alerting
"""

import time
import threading
import logging
import psutil
import json
from typing import Dict, List, Optional
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from .config import Config
from .mainnet_blockchain import MainnetBlockchain
from .mainnet_network import MainnetNetworkNode

logger = logging.getLogger(__name__)

class MainnetMonitoring:
    """Production monitoring system for GSC blockchain"""
    
    def __init__(self, blockchain: MainnetBlockchain, network: MainnetNetworkNode):
        self.blockchain = blockchain
        self.network = network
        self.running = False
        self.monitor_thread = None
        
        # Prometheus metrics
        self.setup_metrics()
        
        # Health status
        self.health_status = {
            'blockchain': True,
            'network': True,
            'system': True,
            'last_check': time.time()
        }
        
        # Alert thresholds
        self.thresholds = {
            'max_memory_usage': 80,  # percentage
            'max_cpu_usage': 90,     # percentage
            'min_peers': 1,          # minimum connected peers
            'max_block_time': 1800,  # 30 minutes
            'max_mempool_size': 10000
        }
    
    def setup_metrics(self):
        """Set up Prometheus metrics"""
        # Blockchain metrics
        self.blockchain_height = Gauge('gsc_blockchain_height', 'Current blockchain height')
        self.blockchain_difficulty = Gauge('gsc_blockchain_difficulty', 'Current mining difficulty')
        self.mempool_size = Gauge('gsc_mempool_size', 'Number of transactions in mempool')
        self.total_supply = Gauge('gsc_total_supply', 'Total GSC coin supply')
        self.blocks_mined = Counter('gsc_blocks_mined_total', 'Total blocks mined')
        self.transactions_processed = Counter('gsc_transactions_processed_total', 'Total transactions processed')
        
        # Network metrics
        self.network_peers = Gauge('gsc_network_peers', 'Number of connected peers')
        self.network_bytes_sent = Counter('gsc_network_bytes_sent_total', 'Total bytes sent')
        self.network_bytes_received = Counter('gsc_network_bytes_received_total', 'Total bytes received')
        self.network_messages_sent = Counter('gsc_network_messages_sent_total', 'Total messages sent')
        self.network_messages_received = Counter('gsc_network_messages_received_total', 'Total messages received')
        
        # System metrics
        self.system_cpu_usage = Gauge('gsc_system_cpu_usage_percent', 'CPU usage percentage')
        self.system_memory_usage = Gauge('gsc_system_memory_usage_percent', 'Memory usage percentage')
        self.system_disk_usage = Gauge('gsc_system_disk_usage_percent', 'Disk usage percentage')
        self.system_uptime = Gauge('gsc_system_uptime_seconds', 'System uptime in seconds')
        
        # Performance metrics
        self.block_processing_time = Histogram('gsc_block_processing_seconds', 'Time to process a block')
        self.transaction_validation_time = Histogram('gsc_transaction_validation_seconds', 'Time to validate a transaction')
        self.network_latency = Histogram('gsc_network_latency_seconds', 'Network message latency')
        
        # Health metrics
        self.health_blockchain = Gauge('gsc_health_blockchain', 'Blockchain health status (1=healthy, 0=unhealthy)')
        self.health_network = Gauge('gsc_health_network', 'Network health status (1=healthy, 0=unhealthy)')
        self.health_system = Gauge('gsc_health_system', 'System health status (1=healthy, 0=unhealthy)')
    
    def start(self, port: int = None):
        """Start monitoring system"""
        if self.running:
            return
        
        port = port or Config.PROMETHEUS_PORT
        
        # Start Prometheus HTTP server
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Monitoring system started")
    
    def stop(self):
        """Stop monitoring system"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("Monitoring system stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        start_time = time.time()
        
        while self.running:
            try:
                # Update metrics
                self._update_blockchain_metrics()
                self._update_network_metrics()
                self._update_system_metrics(start_time)
                
                # Check health
                self._check_health()
                
                # Sleep for monitoring interval
                time.sleep(Config.HEALTH_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _update_blockchain_metrics(self):
        """Update blockchain-related metrics"""
        try:
            # Basic blockchain metrics
            self.blockchain_height.set(len(self.blockchain.chain))
            self.blockchain_difficulty.set(self.blockchain.difficulty)
            self.mempool_size.set(len(self.blockchain.mempool))
            
            # Calculate total supply
            total_supply = sum(self.blockchain.balances.values())
            self.total_supply.set(total_supply)
            
            # Update counters from blockchain metrics
            metrics = self.blockchain.metrics
            self.blocks_mined._value._value = metrics.get('blocks_mined', 0)
            self.transactions_processed._value._value = metrics.get('transactions_processed', 0)
            
        except Exception as e:
            logger.error(f"Error updating blockchain metrics: {e}")
    
    def _update_network_metrics(self):
        """Update network-related metrics"""
        try:
            # Peer count
            self.network_peers.set(len(self.network.peers))
            
            # Network statistics
            stats = self.network.stats
            self.network_bytes_sent._value._value = stats.get('bytes_sent', 0)
            self.network_bytes_received._value._value = stats.get('bytes_received', 0)
            self.network_messages_sent._value._value = stats.get('messages_sent', 0)
            self.network_messages_received._value._value = stats.get('messages_received', 0)
            
        except Exception as e:
            logger.error(f"Error updating network metrics: {e}")
    
    def _update_system_metrics(self, start_time: float):
        """Update system-related metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_usage.set(disk_percent)
            
            # Uptime
            uptime = time.time() - start_time
            self.system_uptime.set(uptime)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def _check_health(self):
        """Perform health checks"""
        current_time = time.time()
        
        # Blockchain health
        blockchain_healthy = True
        try:
            # Check if blockchain is valid
            is_valid, _ = self.blockchain.is_chain_valid()
            if not is_valid:
                blockchain_healthy = False
                logger.warning("Blockchain validation failed")
            
            # Check block time
            if len(self.blockchain.chain) > 1:
                latest_block = self.blockchain.chain[-1]
                block_age = current_time - latest_block.timestamp
                if block_age > self.thresholds['max_block_time']:
                    blockchain_healthy = False
                    logger.warning(f"Last block is {block_age:.0f} seconds old")
            
            # Check mempool size
            if len(self.blockchain.mempool) > self.thresholds['max_mempool_size']:
                blockchain_healthy = False
                logger.warning(f"Mempool size ({len(self.blockchain.mempool)}) exceeds threshold")
                
        except Exception as e:
            blockchain_healthy = False
            logger.error(f"Blockchain health check failed: {e}")
        
        # Network health
        network_healthy = True
        try:
            # Check peer count
            peer_count = len(self.network.peers)
            if peer_count < self.thresholds['min_peers']:
                network_healthy = False
                logger.warning(f"Low peer count: {peer_count}")
            
            # Check if network is running
            if not self.network.running:
                network_healthy = False
                logger.warning("Network node is not running")
                
        except Exception as e:
            network_healthy = False
            logger.error(f"Network health check failed: {e}")
        
        # System health
        system_healthy = True
        try:
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.thresholds['max_memory_usage']:
                system_healthy = False
                logger.warning(f"High memory usage: {memory.percent:.1f}%")
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent()
            if cpu_percent > self.thresholds['max_cpu_usage']:
                system_healthy = False
                logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                
        except Exception as e:
            system_healthy = False
            logger.error(f"System health check failed: {e}")
        
        # Update health status
        self.health_status.update({
            'blockchain': blockchain_healthy,
            'network': network_healthy,
            'system': system_healthy,
            'last_check': current_time
        })
        
        # Update health metrics
        self.health_blockchain.set(1 if blockchain_healthy else 0)
        self.health_network.set(1 if network_healthy else 0)
        self.health_system.set(1 if system_healthy else 0)
        
        # Log overall health
        overall_healthy = blockchain_healthy and network_healthy and system_healthy
        if not overall_healthy:
            logger.warning("System health check failed")
        else:
            logger.debug("System health check passed")
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        return {
            'status': self.health_status,
            'thresholds': self.thresholds,
            'overall_healthy': all(self.health_status[k] for k in ['blockchain', 'network', 'system'])
        }
    
    def get_metrics_summary(self) -> Dict:
        """Get summary of key metrics"""
        try:
            return {
                'blockchain': {
                    'height': len(self.blockchain.chain),
                    'difficulty': self.blockchain.difficulty,
                    'mempool_size': len(self.blockchain.mempool),
                    'total_supply': sum(self.blockchain.balances.values())
                },
                'network': {
                    'peers': len(self.network.peers),
                    'uptime': self.network.stats.get('uptime', 0),
                    'bytes_sent': self.network.stats.get('bytes_sent', 0),
                    'bytes_received': self.network.stats.get('bytes_received', 0)
                },
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
                }
            }
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}
    
    def record_block_processing_time(self, duration: float):
        """Record block processing time"""
        self.block_processing_time.observe(duration)
    
    def record_transaction_validation_time(self, duration: float):
        """Record transaction validation time"""
        self.transaction_validation_time.observe(duration)
    
    def record_network_latency(self, duration: float):
        """Record network message latency"""
        self.network_latency.observe(duration)

class AlertManager:
    """Alert management system"""
    
    def __init__(self, monitoring: MainnetMonitoring):
        self.monitoring = monitoring
        self.alerts = []
        self.alert_history = []
        self.running = False
        self.alert_thread = None
    
    def start(self):
        """Start alert manager"""
        if self.running:
            return
        
        self.running = True
        self.alert_thread = threading.Thread(target=self._alert_loop, daemon=True)
        self.alert_thread.start()
        
        logger.info("Alert manager started")
    
    def stop(self):
        """Stop alert manager"""
        if not self.running:
            return
        
        self.running = False
        if self.alert_thread and self.alert_thread.is_alive():
            self.alert_thread.join(timeout=5)
        
        logger.info("Alert manager stopped")
    
    def _alert_loop(self):
        """Main alert checking loop"""
        while self.running:
            try:
                self._check_alerts()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Alert manager error: {e}")
                time.sleep(60)
    
    def _check_alerts(self):
        """Check for alert conditions"""
        health_status = self.monitoring.get_health_status()
        
        # Check for unhealthy components
        for component, healthy in health_status['status'].items():
            if component == 'last_check':
                continue
            
            if not healthy:
                alert = {
                    'type': 'health',
                    'component': component,
                    'message': f"{component.title()} is unhealthy",
                    'severity': 'critical',
                    'timestamp': time.time()
                }
                self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Dict):
        """Trigger an alert"""
        # Add to current alerts if not already present
        existing = any(
            a['type'] == alert['type'] and a['component'] == alert['component']
            for a in self.alerts
        )
        
        if not existing:
            self.alerts.append(alert)
            self.alert_history.append(alert)
            
            # Log alert
            logger.error(f"ALERT: {alert['message']} (severity: {alert['severity']})")
            
            # Here you could add integrations with:
            # - Email notifications
            # - Slack/Discord webhooks
            # - PagerDuty
            # - SMS alerts
    
    def get_active_alerts(self) -> List[Dict]:
        """Get active alerts"""
        return self.alerts
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    def clear_alert(self, alert_type: str, component: str):
        """Clear a specific alert"""
        self.alerts = [
            a for a in self.alerts 
            if not (a['type'] == alert_type and a['component'] == component)
        ]
