import json
import os
import time
from functools import lru_cache, wraps
from http.client import HTTPException

import requests

# from autogpt.config.config import Config


CACHE_TOKEN_TIMEOUT = 3600




# def refresh_credentials(config:Config):
#     import llm_commons.btp_llm as btp_llm
#     names = ('client_id', 'client_secret', 'auth_url', 'api_base', 'token')
#     for name in names:
#         setattr(btp_llm, name, from_conf(name.upper()))


# def from_conf(config, name, default=None, validate_fn=None, prefix='BTP_LLM'):
#     env_name = f'{prefix}_{name}'
#     value = os.environ.get(env_name, config.get(env_name, default))
#     if validate_fn and value is not None:
#         validate_fn(env_name, value)
#     return value


def get_token(auth_url=None, client_id=None, client_secret=None):
    """Get a token from XSUAA.
    :param auth_url: URL of the XSUAA service
    :param client_id: Client ID of the service instance
    :param client_secret: Client secret of the service instance
    :return: Access token
    """
    auth_url = auth_url #or btp_llm.auth_url
    if not auth_url:
        raise ValueError(
            'Either explicitly provide a value for auth_url, set llm_commons.btp_llm.auth_url or use environment variable BTP_LLM_AUTH_URL'
        )
    client_id = client_id #or btp_llm.client_id
    if not client_id:
        raise ValueError(
            'Either explicitly provide a value for client_id, set llm_commons.btp_llm.client_id or use environment variable BTP_LLM_CLIENT_ID'
        )
    client_secret = client_secret #or btp_llm.client_secret
    if not client_secret:
        raise ValueError(
            'Either explicitly provide a value for client_secret, set llm_commons.btp_llm.client_secret or use environment variable BTP_LLM_CLIENT_SECRET'
        )

    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }
    response = requests.post(auth_url + '?grant_type=client_credentials', data=data, timeout=5)
    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token']
    raise HTTPException(f'status_code={response.status_code}, detail={response.text}')


def _lru_cache_timeout(timeout=60):
    caching_times = []

    def wrapper(func):

        @lru_cache()
        def f_cached(_time, *args, **kwargs):
            return func(*args, **kwargs)

        @wraps(func)
        def f_wrapped(*args, _uncached=False, **kwargs):
            _time = time.time()
            if len(caching_times) == 0:
                caching_times.append(_time)
            elif (_time - caching_times[0]) > timeout or _uncached:
                caching_times[0] = _time
            return f_cached(caching_times[0], *args, **kwargs)

        return f_wrapped

    return wrapper

get_token_cached = _lru_cache_timeout(CACHE_TOKEN_TIMEOUT)(get_token)