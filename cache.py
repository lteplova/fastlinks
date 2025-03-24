import redis
from config import REDIS_HOST, REDIS_PORT

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

# достает из кэша ссылку
def get_cached_url(short_code):
    short_code = str(short_code)
    return redis_client.get(short_code)

# кэширует
def cache_url(short_code, original_url):
    short_code = str(short_code)
    original_url = str(original_url)
    redis_client.setex(short_code, 3600, original_url)

def delete_cached_link(short_code):
    redis_client.delete(short_code)

# достает из кэша короткую ссылку
def get_cached_link(original_url):
    original_url = str(original_url)
    return redis_client.get(original_url)

# кэширует
def cache_link(original_url, short_code):
    short_code = str(short_code)
    original_url = str(original_url)
    redis_client.setex(original_url, 3600, short_code)
