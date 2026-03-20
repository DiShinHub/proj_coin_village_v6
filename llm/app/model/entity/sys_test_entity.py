from sqlalchemy import Column, Integer, TIMESTAMP, String

from app.config.database_config.database_config_repository import Base


class SysTestEntity(Base):
    __tablename__ = "sys_test"
    seq = Column(Integer, primary_key=True)
    string1 = Column(String(10))
    string2 = Column(String(10))
    string3 = Column(String(10))
    string4 = Column(String(10))
    string5 = Column(String(10))
    reg_dt = Column(TIMESTAMP(timezone=True))
    mod_dt = Column(TIMESTAMP(timezone=True))
