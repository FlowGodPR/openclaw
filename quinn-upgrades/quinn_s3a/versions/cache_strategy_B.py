
# Version B: TTL Cache
def cache_get(key):
    return ttl_cache.get(key) if not ttl_cache.expired(key) else None
