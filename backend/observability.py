"""
Advanced Observability and Monitoring
Health checks, metrics, and performance monitoring for enterprise deployment
"""
from fastapi import Request, Response
from typing import Dict, Any, Optional
import time
import psutil
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import logging

logger = logging.getLogger(__name__)

class SystemMetrics:
    """System performance metrics collector"""
    
    def __init__(self):
        self.request_metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'errors': 0,
            'last_request': None
        })
        self.response_times = deque(maxlen=1000)  # Keep last 1000 response times
        self.error_counts = defaultdict(int)
        self.tenant_metrics = defaultdict(lambda: {
            'requests': 0,
            'errors': 0,
            'avg_response_time': 0
        })
    
    def record_request(self, method: str, path: str, status_code: int, 
                      response_time: float, tenant_id: Optional[str] = None):
        """Record request metrics"""
        endpoint = f"{method} {path}"
        
        # Update endpoint metrics
        metrics = self.request_metrics[endpoint]
        metrics['count'] += 1
        metrics['total_time'] += response_time
        metrics['last_request'] = datetime.utcnow()
        
        if status_code >= 400:
            metrics['errors'] += 1
            self.error_counts[status_code] += 1
        
        # Update response times
        self.response_times.append(response_time)
        
        # Update tenant metrics
        if tenant_id:
            tenant_stats = self.tenant_metrics[tenant_id]
            tenant_stats['requests'] += 1
            if status_code >= 400:
                tenant_stats['errors'] += 1
            
            # Update average response time
            old_avg = tenant_stats['avg_response_time']
            count = tenant_stats['requests']
            tenant_stats['avg_response_time'] = (old_avg * (count - 1) + response_time) / count
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Response time statistics
            response_times_list = list(self.response_times)
            avg_response_time = sum(response_times_list) / len(response_times_list) if response_times_list else 0
            
            # Calculate percentiles
            if response_times_list:
                sorted_times = sorted(response_times_list)
                p50 = sorted_times[len(sorted_times) // 2] if sorted_times else 0
                p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
                p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
            else:
                p50 = p95 = p99 = 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning",
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "used": memory.used
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100
                    }
                },
                "performance": {
                    "avg_response_time": avg_response_time,
                    "response_time_p50": p50,
                    "response_time_p95": p95,
                    "response_time_p99": p99,
                    "total_requests": sum(m['count'] for m in self.request_metrics.values()),
                    "total_errors": sum(m['errors'] for m in self.request_metrics.values()),
                    "error_rate": self._calculate_error_rate()
                },
                "tenants": dict(self.tenant_metrics),
                "top_endpoints": self._get_top_endpoints(),
                "error_breakdown": dict(self.error_counts)
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def _calculate_error_rate(self) -> float:
        """Calculate overall error rate"""
        total_requests = sum(m['count'] for m in self.request_metrics.values())
        total_errors = sum(m['errors'] for m in self.request_metrics.values())
        return (total_errors / total_requests * 100) if total_requests > 0 else 0
    
    def _get_top_endpoints(self, limit: int = 10) -> Dict[str, Dict]:
        """Get top endpoints by request count"""
        sorted_endpoints = sorted(
            self.request_metrics.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        result = {}
        for endpoint, metrics in sorted_endpoints[:limit]:
            result[endpoint] = {
                'requests': metrics['count'],
                'errors': metrics['errors'],
                'avg_response_time': metrics['total_time'] / metrics['count'] if metrics['count'] > 0 else 0,
                'error_rate': (metrics['errors'] / metrics['count'] * 100) if metrics['count'] > 0 else 0,
                'last_request': metrics['last_request'].isoformat() if metrics['last_request'] else None
            }
        
        return result

# Global metrics instance
metrics_collector = SystemMetrics()

class ObservabilityMiddleware:
    """Middleware for collecting observability metrics"""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Get tenant ID from request state
        tenant_id = getattr(request.state, 'tenant_id', None)
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Record metrics
        metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time=response_time,
            tenant_id=tenant_id
        )
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{response_time:.3f}"
        if tenant_id:
            response.headers["X-Tenant-ID"] = tenant_id
        
        return response

async def get_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance"""
    try:
        from .server import db  # Import db from server
        
        start_time = time.time()
        
        # Test basic connectivity
        await db.users.find_one({"email": "admin@demo.com"})
        
        response_time = time.time() - start_time
        
        # Get database stats
        stats = await db.command("dbStats")
        
        return {
            "status": "healthy",
            "response_time": response_time,
            "collections": stats.get("collections", 0),
            "objects": stats.get("objects", 0),
            "data_size": stats.get("dataSize", 0),
            "index_size": stats.get("indexSize", 0),
            "storage_size": stats.get("storageSize", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def get_tenant_health() -> Dict[str, Any]:
    """Check tenant-specific health metrics"""
    try:
        from .server import db
        
        # Count tenants
        tenant_count = await db.tenants.count_documents({})
        
        # Count active tenants (have recent activity)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        active_tenants = len([
            tenant_id for tenant_id, metrics in metrics_collector.tenant_metrics.items()
            if metrics['requests'] > 0
        ])
        
        # Get tenant with most requests
        busiest_tenant = max(
            metrics_collector.tenant_metrics.items(),
            key=lambda x: x[1]['requests'],
            default=(None, None)
        )
        
        return {
            "status": "healthy",
            "total_tenants": tenant_count,
            "active_tenants": active_tenants,
            "busiest_tenant": {
                "tenant_id": busiest_tenant[0],
                "requests": busiest_tenant[1]['requests'] if busiest_tenant[1] else 0
            } if busiest_tenant[0] else None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def get_security_health() -> Dict[str, Any]:
    """Check security-related health metrics"""
    try:
        # Count recent errors by type
        auth_errors = metrics_collector.error_counts.get(401, 0)
        forbidden_errors = metrics_collector.error_counts.get(403, 0)
        server_errors = sum(
            count for status_code, count in metrics_collector.error_counts.items()
            if status_code >= 500
        )
        
        # Calculate security score
        total_requests = sum(m['count'] for m in metrics_collector.request_metrics.values())
        security_incidents = auth_errors + forbidden_errors
        security_score = max(0, 100 - (security_incidents / max(total_requests, 1) * 100))
        
        return {
            "status": "healthy" if security_score > 95 else "warning",
            "security_score": security_score,
            "auth_errors": auth_errors,
            "forbidden_errors": forbidden_errors,
            "server_errors": server_errors,
            "total_requests": total_requests
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }