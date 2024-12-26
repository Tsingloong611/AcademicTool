from database.db_config import engine
from models import Base  # 或者 from models import <所有ORM类>

Base.metadata.create_all(engine)
