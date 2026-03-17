import time
import hashlib
import json
from functools import wraps
from typing import Any, Optional


class MemoryCache:
    def __init__(self, default_ttl: int = 300):  
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, expiry = self.cache[key]
            if expiry > time.time():
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if ttl is None:
            ttl = self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()


cache = MemoryCache()

def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
           
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            key = hashlib.md5("".join(key_parts).encode()).hexdigest()
            
            
            result = cache.get(key)
            if result is not None:
                return result
            
           
            result = func(*args, **kwargs)
            
            
            cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator