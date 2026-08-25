"""
Configuration module for Zero-Config Local Network & Hotspot File Transfer.
Handles local IP / Mobile Hotspot auto-detection, QR code generation, and Zeroconf discovery.
100% Offline - 0 Data Usage over Local Wi-Fi and Personal Hotspot.
"""

import os
import socket
import logging
import shutil
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Server & Transfer configuration
DEFAULT_PORT: int = 53317
MAX_CONCURRENT_UPLOADS: int = 50
CHUNK_SIZE: int = 4 * 1024 * 1024  # 4MB chunks for high-throughput 30GB+ transfers
MAX_FILE_SIZE: int = 35 * 1024 * 1024 * 1024  # 35 GB max file size support
UPLOAD_DIR: str = "uploads"

# Database configuration
DB_PATH: str = "database/transfers.db"

# Virtual adapter prefixes to exclude (Docker, VirtualBox, link-local)
EXCLUDED_PREFIXES = (
    '127.',           # localhost
    '169.254.',      # link-local
    '172.17.',       # Docker bridge
    '172.18.',       # Docker bridge
    '172.19.',       # Docker bridge
    '172.21.',       # Docker bridge
    '172.22.',       # Docker bridge
    '172.23.',       # Docker bridge
    '192.168.56.',   # VirtualBox Host-Only
    '10.0.2.',       # VirtualBox NAT
    '10.0.3.',       # VirtualBox NAT
)

# Known mobile hotspot subnets
HOTSPOT_PREFIXES = (
    '192.168.43.',   # Android Portable Hotspot default
    '172.20.10.',    # iOS Personal Hotspot default
    '192.168.137.',  # Windows Mobile Hotspot default
    '192.168.44.',   # Secondary Android AP
    '192.168.49.',   # Wi-Fi Direct (P2P Android)
)


def get_all_local_ips() -> List[Dict[str, str]]:
    """
    Enumerate all valid network interfaces and classify them
    (Hotspot, Wi-Fi, Ethernet, LAN).
    """
    results = []
    seen_ips = set()
    
    try:
        import ifaddr
        for adapter in ifaddr.get_adapters():
            for addr in adapter.ips:
                if getattr(addr, 'is_IPv4', False):
                    ip = addr.ip
                    if not isinstance(ip, str) or ip in seen_ips:
                        continue
                    
                    # Skip excluded virtual adapters
                    if any(ip.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
                        continue
                    
                    seen_ips.add(ip)
                    name = adapter.nice_name or adapter.name
                    
                    # Classify connection type
                    is_hotspot = any(ip.startswith(prefix) for prefix in HOTSPOT_PREFIXES)
                    if is_hotspot:
                        conn_type = "Mobile Hotspot"
                    elif any(k in name.lower() for k in ('wi-fi', 'wireless', 'wlan', 'wl')):
                        conn_type = "Wi-Fi LAN"
                    elif any(k in name.lower() for k in ('eth', 'en', 'ethernet', 'lan')):
                        conn_type = "Ethernet LAN"
                    else:
                        conn_type = "Local Network"
                        
                    results.append({
                        "ip": ip,
                        "adapter": name,
                        "type": conn_type,
                        "is_hotspot": is_hotspot
                    })
    except Exception as e:
        logger.warning(f"Error enumerating with ifaddr: {e}")

    # Fallback to UDP socket inspection if no adapters detected
    if not results:
        fallback_ip = get_socket_ip()
        if fallback_ip and fallback_ip not in seen_ips:
            is_hotspot = any(fallback_ip.startswith(prefix) for prefix in HOTSPOT_PREFIXES)
            results.append({
                "ip": fallback_ip,
                "adapter": "Default Gateway",
                "type": "Mobile Hotspot" if is_hotspot else "Wi-Fi / LAN",
                "is_hotspot": is_hotspot
            })

    # Ultimate localhost fallback
    if not results:
        results.append({
            "ip": "127.0.0.1",
            "adapter": "Loopback",
            "type": "Localhost Only",
            "is_hotspot": False
        })

    # Sort so Hotspots and Wi-Fi appear first
    results.sort(key=lambda x: (not x["is_hotspot"], "Wi-Fi" not in x["type"]))
    return results


def get_socket_ip() -> str:
    """Determine outbound IP using socket routing query without sending packets."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.5)
        try:
            # Query standard LAN DNS target without transmitting data
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if not any(ip.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
                return ip
        finally:
            s.close()
    except Exception:
        pass
    return "127.0.0.1"


def get_local_ip() -> str:
    """Get the primary local or hotspot IP address."""
    ips = get_all_local_ips()
    # If a hotspot interface is detected, prioritize it
    for item in ips:
        if item["is_hotspot"]:
            return item["ip"]
    return ips[0]["ip"] if ips else "127.0.0.1"


def get_storage_stats() -> Dict[str, Any]:
    """Return storage stats for the upload partition."""
    upload_path = ensure_upload_dir()
    try:
        total, used, free = shutil.disk_usage(upload_path)
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "free_gb": round(free / (1024 ** 3), 2),
            "total_gb": round(total / (1024 ** 3), 2),
            "percent_used": round((used / total) * 100, 1)
        }
    except Exception as e:
        logger.error(f"Error checking disk usage: {e}")
        return {
            "total_bytes": 0,
            "used_bytes": 0,
            "free_bytes": 0,
            "free_gb": 0,
            "total_gb": 0,
            "percent_used": 0
        }


def ensure_upload_dir() -> str:
    """Create uploads directory if it does not exist."""
    upload_path = os.path.join(os.path.dirname(__file__), "..", UPLOAD_DIR)
    os.makedirs(upload_path, exist_ok=True)
    return upload_path


class ZeroconfService:
    """mDNS service discovery via Python-Zeroconf for Apple Bonjour / Android LAN."""
    
    def __init__(self, name: str, port: int):
        self.service_name = name
        self.port = port
        self.zeroconf = None
        self.service_info = None
    
    def publish(self, local_ip: str) -> bool:
        """Broadcast mDNS service record in background thread."""
        import threading
        
        def _do_publish():
            try:
                from zeroconf import Zeroconf, ServiceInfo
                
                service_type = "_http._tcp.local."
                service_name = f"{self.service_name}.{service_type}"
                self.service_info = ServiceInfo(
                    service_type,
                    name=service_name,
                    server="lightshare.local.",
                    port=self.port,
                    properties={
                        b'server': b'LightShare',
                        b'version': b'1.0.0',
                        b'protocol': b'http'
                    },
                    addresses=[socket.inet_aton(local_ip)]
                )
                self.zeroconf = Zeroconf()
                self.zeroconf.register_service(self.service_info)
                logger.info(f"mDNS service published: {service_name} on {local_ip}:{self.port}")
            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"mDNS service info: {e}")

        t = threading.Thread(target=_do_publish, daemon=True)
        t.start()
        return True
    
    def unpublish(self) -> None:
        """Stop mDNS broadcasting."""
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            except Exception:
                pass