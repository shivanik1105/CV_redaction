"""
Rate Limiter for LLM API Calls
Tracks API usage and enforces rate limits using Redis
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for LLM API calls using Redis"""
    
    # Default rate limits (requests per minute)
    DEFAULT_LIMITS = {
        "gemini": {"rpm": 10, "rpd": 1500},  # Free tier
        "openai": {"rpm": 3, "rpd": 200},     # Free tier
        "anthropic": {"rpm": 5, "rpd": 1000}, # Free tier
        "ollama": {"rpm": 1000, "rpd": 100000}  # Local, no limits
    }
    
    def __init__(
        self,
        redis_client: Redis,
        custom_limits: Dict[str, Dict[str, int]] = None
    ):
        """
        Initialize Rate Limiter
        
        Args:
            redis_client: Redis client instance
            custom_limits: Custom rate limits per provider
                          Format: {"provider": {"rpm": X, "rpd": Y}}
        """
        self.redis = redis_client
        self.limits = {**self.DEFAULT_LIMITS}
        
        if custom_limits:
            self.limits.update(custom_limits)
        
        logger.info(f"Rate limiter initialized with limits: {self.limits}")
    
    def check_quota(self, provider: str) -> bool:
        """
        Check if API quota is available for provider
        
        Args:
            provider: API provider name (gemini, openai, anthropic, ollama)
        
        Returns:
            True if quota available, False if rate limited
        """
        if provider not in self.limits:
            logger.warning(f"Unknown provider {provider}, allowing request")
            return True
        
        limits = self.limits[provider]
        
        # Check minute limit
        minute_key = f"ratelimit:{provider}:minute:{datetime.now().strftime('%Y%m%d%H%M')}"
        minute_count = int(self.redis.get(minute_key) or 0)
        
        if minute_count >= limits["rpm"]:
            logger.warning(f"Rate limit exceeded for {provider}: {minute_count}/{limits['rpm']} RPM")
            return False
        
        # Check daily limit
        day_key = f"ratelimit:{provider}:day:{datetime.now().strftime('%Y%m%d')}"
        day_count = int(self.redis.get(day_key) or 0)
        
        if day_count >= limits["rpd"]:
            logger.warning(f"Daily quota exceeded for {provider}: {day_count}/{limits['rpd']} RPD")
            return False
        
        return True
    
    def record_api_call(self, provider: str) -> None:
        """
        Record an API call for rate limiting
        
        Args:
            provider: API provider name
        """
        if provider not in self.limits:
            return
        
        try:
            # Increment minute counter
            minute_key = f"ratelimit:{provider}:minute:{datetime.now().strftime('%Y%m%d%H%M')}"
            self.redis.incr(minute_key)
            self.redis.expire(minute_key, 120)  # Expire after 2 minutes
            
            # Increment daily counter
            day_key = f"ratelimit:{provider}:day:{datetime.now().strftime('%Y%m%d')}"
            self.redis.incr(day_key)
            self.redis.expire(day_key, 86400 * 2)  # Expire after 2 days
            
            # Update last call timestamp
            self.redis.set(f"ratelimit:{provider}:last_call", datetime.now().isoformat())
            
            logger.debug(f"Recorded API call for {provider}")
            
        except RedisError as e:
            logger.error(f"Failed to record API call: {e}")
    
    def get_wait_time(self, provider: str) -> int:
        """
        Get wait time in seconds before next API call is allowed
        
        Args:
            provider: API provider name
        
        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        if provider not in self.limits:
            return 0
        
        limits = self.limits[provider]
        
        # Check minute limit
        minute_key = f"ratelimit:{provider}:minute:{datetime.now().strftime('%Y%m%d%H%M')}"
        minute_count = int(self.redis.get(minute_key) or 0)
        
        if minute_count >= limits["rpm"]:
            # Wait until next minute
            now = datetime.now()
            next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
            wait_seconds = int((next_minute - now).total_seconds())
            return wait_seconds
        
        # Check daily limit
        day_key = f"ratelimit:{provider}:day:{datetime.now().strftime('%Y%m%d')}"
        day_count = int(self.redis.get(day_key) or 0)
        
        if day_count >= limits["rpd"]:
            # Wait until next day
            now = datetime.now()
            next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            wait_seconds = int((next_day - now).total_seconds())
            return wait_seconds
        
        # Calculate safe wait time to avoid hitting RPM limit
        # Add 6 seconds between calls for 10 RPM (60s / 10 = 6s)
        safe_wait = 60 // limits["rpm"] if limits["rpm"] > 0 else 0
        
        # Check last call time
        last_call_str = self.redis.get(f"ratelimit:{provider}:last_call")
        if last_call_str:
            try:
                last_call = datetime.fromisoformat(last_call_str)
                elapsed = (datetime.now() - last_call).total_seconds()
                if elapsed < safe_wait:
                    return int(safe_wait - elapsed)
            except (ValueError, TypeError):
                pass
        
        return 0
    
    def get_usage_stats(self, provider: str) -> Dict:
        """
        Get current usage statistics for provider
        
        Args:
            provider: API provider name
        
        Returns:
            Dictionary with usage stats
        """
        if provider not in self.limits:
            return {}
        
        limits = self.limits[provider]
        
        # Get current counts
        minute_key = f"ratelimit:{provider}:minute:{datetime.now().strftime('%Y%m%d%H%M')}"
        minute_count = int(self.redis.get(minute_key) or 0)
        
        day_key = f"ratelimit:{provider}:day:{datetime.now().strftime('%Y%m%d')}"
        day_count = int(self.redis.get(day_key) or 0)
        
        # Calculate percentages
        minute_percent = round(minute_count / limits["rpm"] * 100, 1) if limits["rpm"] > 0 else 0
        day_percent = round(day_count / limits["rpd"] * 100, 1) if limits["rpd"] > 0 else 0
        
        return {
            "provider": provider,
            "minute_usage": f"{minute_count}/{limits['rpm']} ({minute_percent}%)",
            "day_usage": f"{day_count}/{limits['rpd']} ({day_percent}%)",
            "minute_remaining": limits["rpm"] - minute_count,
            "day_remaining": limits["rpd"] - day_count,
            "wait_time_seconds": self.get_wait_time(provider),
            "quota_available": self.check_quota(provider)
        }
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """
        Get usage statistics for all providers
        
        Returns:
            Dictionary mapping provider names to their stats
        """
        return {
            provider: self.get_usage_stats(provider)
            for provider in self.limits.keys()
        }
    
    def reset_quota(self, provider: str, scope: str = "all") -> bool:
        """
        Reset quota counters for provider (admin function)
        
        Args:
            provider: API provider name
            scope: "minute", "day", or "all"
        
        Returns:
            True if reset successfully
        """
        try:
            if scope in ["minute", "all"]:
                minute_key = f"ratelimit:{provider}:minute:{datetime.now().strftime('%Y%m%d%H%M')}"
                self.redis.delete(minute_key)
            
            if scope in ["day", "all"]:
                day_key = f"ratelimit:{provider}:day:{datetime.now().strftime('%Y%m%d')}"
                self.redis.delete(day_key)
            
            logger.info(f"Reset {scope} quota for {provider}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to reset quota: {e}")
            return False
    
    def update_limits(self, provider: str, rpm: int = None, rpd: int = None) -> bool:
        """
        Update rate limits for provider (admin function)
        
        Args:
            provider: API provider name
            rpm: Requests per minute (optional)
            rpd: Requests per day (optional)
        
        Returns:
            True if updated successfully
        """
        if provider not in self.limits:
            self.limits[provider] = {"rpm": 10, "rpd": 1000}
        
        if rpm is not None:
            self.limits[provider]["rpm"] = rpm
        
        if rpd is not None:
            self.limits[provider]["rpd"] = rpd
        
        logger.info(f"Updated limits for {provider}: {self.limits[provider]}")
        return True
