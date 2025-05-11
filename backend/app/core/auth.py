# app/core/auth.py
import json
import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt

load_dotenv("/home/om/temp/intern-project/backend/.env")

clerk_issuer = os.getenv("CLERK_ISSUER")
clerk_jwks = os.getenv("CLERK_JWKS")
clerk_secret_key = os.getenv("CLERK_SECRET_KEY")

security = HTTPBearer()


def get_jwks():
    response = json.loads(clerk_jwks)
    return response


def get_public_key(kid):
    jwks = get_jwks()
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return jwk.construct(key)
    raise HTTPException(status_code=401, detail="Invalid token")


def decode_token(token: str):
    headers = jwt.get_unverified_headers(token)
    kid = headers["kid"]
    public_key = get_public_key(kid)
    return jwt.decode(
        token,
        public_key.to_pem().decode("utf-8"),
        algorithms=["RS256"],
        audience="your_audience",
        issuer=clerk_issuer,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    payload = decode_token(token)
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    return clerk_id


async def get_current_clerk_id(token: str):
    payload = decode_token(token)
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    return clerk_id
