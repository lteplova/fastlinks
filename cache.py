import json


# кэширует
def create_cache_url(short_code, original_url, clicks, expires_at, redis_client, last_accessed=0):

    data = {
        'original_url': original_url,
        'short_code': short_code,
        'clicks': clicks,
        'expires_at': str(expires_at),
        'last_accessed': str(last_accessed)
    }

    json_data = json.dumps(data)
    print(json_data)

    redis_client.setex(short_code, 3600, json_data)


# забирает из кэша
def get_cached_url(short_code, redis_client):
    short_code = str(short_code)
    cached_data = redis_client.get(short_code)

    if cached_data is not None:
        try:
            data = json.loads(cached_data)
            return data
        except json.JSONDecodeError:
            return None
    else:

        return None

# удаляет из кэша
def delete_cached_link(short_code, redis_client):
    print(short_code)
    redis_client.delete(short_code)
