import sys
sys.path.append('C:\\Agent RAB Analyzer\\backend_fastapi')

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

try:
    db = SessionLocal()
    hashed_pwd = get_password_hash("password123")
    new_user = User(username="test_admin", email="test_admin@kalsel.com", hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
