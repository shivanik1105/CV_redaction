"""
DNS fix for JioFiber ISP DNS hijacking.
JioFiber returns wrong IPv6 address for Supabase domains.
This module patches Python's DNS resolution to use correct Cloudflare IPs.
Import this BEFORE any Supabase/httpx imports.
"""
import socket

# Correct IPs from Google DNS (8.8.8.8) for Supabase
DNS_OVERRIDES = {
    "dpnvwxsslvasyufwqzwr.supabase.co": [
        ("104.18.38.10", 443),
        ("172.64.149.246", 443),
    ]
}

_original_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """Override DNS for specific hostnames with known-good IPs."""
    if host in DNS_OVERRIDES:
        results = []
        for ip, _default_port in DNS_OVERRIDES[host]:
            actual_port = port if port else _default_port
            results.append((
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,  # IPPROTO_TCP
                '',
                (ip, actual_port)
            ))
        return results
    return _original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _patched_getaddrinfo
