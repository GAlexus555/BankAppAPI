from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import DBAccount, Role
import hashlib
import base64

SECRET_KEY = "4Ag%4!.hro,ok!siri!wieheisstjohnpork!.y7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _prepare_password(password: str) -> str:
    digest = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(digest).decode()

def hash_password(password: str) -> str:
    return pwd_context.hash(_prepare_password(password))

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_prepare_password(plain), hashed)

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


auth_scheme = OAuth2PasswordBearer(tokenUrl="/accounts/login")

def get_current_user(token: str = Depends(auth_scheme), db: Session = Depends(get_db)) -> DBAccount:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

    # Versuchen den email aus den Token rauszulesen
    try:
        input = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = input.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Den user raus holen
    user = db.query(DBAccount).filter(DBAccount.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email has not been found!")
    return user

def require_role(required_role: Role):
    # Funktion um Rolle von authentifizierten User raus zu lesen
    def checker(current_user: DBAccount = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{required_role} ist notig!")
        return current_user

    return checker