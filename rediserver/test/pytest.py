import pytest
from .server import local_redis as local_redis_server


@pytest.fixture(scope='function')
def local_redis():
    with local_redis_server() as redis_proxy:
        yield redis_proxy
