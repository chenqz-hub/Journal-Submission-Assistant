import os
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

api_key_header = APIKeyHeader(name='X-Access-Code', auto_error=False)

def verify_access_code(access_code: str = Security(api_key_header)):
    expected_code = os.getenv('ACCESS_CODE', '')
    if expected_code and access_code != expected_code:
        raise HTTPException(status_code=403, detail='口令错误或未提供口令')
    return True
