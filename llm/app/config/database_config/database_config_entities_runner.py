from sqlalchemy.engine import Engine

from app.config.database_config.database_config_repository import Base
from app.model.entity.mbr_member_auth_jwt_entity import MbrMemberAuthJwtEntity
from app.model.entity.mbr_member_entity import MbrMemberEntity
from app.model.entity.mbr_member_role_entity import MbrMemberRoleEntity
from app.model.entity.sys_test_entity import SysTestEntity
from app.tool.log_tool import LogTool


class DatabaseConfigEntitiesRunner:
    __logger = LogTool.get_logger(__qualname__)

    __engine: Engine

    def __init__(self, engine: Engine = None):
        self.__logger.info("Initialize Database Config Entities Runner")
        self.__engine = engine

    def _keep_reference(self):
        self.sys_test = SysTestEntity()
        self.mbr_member = MbrMemberEntity()
        self.mbr_member_auth_jwt = MbrMemberAuthJwtEntity()
        self.mbr_member_role = MbrMemberRoleEntity()

    def run_sync(self) -> None:
        self.__logger.info("Run Database Config Entities Start with Sync Engine")
        self.run_sync_drop_all()
        self.run_sync_create_all()

    def run_sync_drop_all(self) -> None:
        Base.metadata.drop_all(bind=self.__engine)

    def run_sync_create_all(self) -> None:
        Base.metadata.create_all(bind=self.__engine)

    async def run_async(self) -> None:
        self.__logger.info("Run Database Config Entities Start with Async Engine")
        await self.run_async_drop_all()
        await self.run_async_create_all()

    async def run_async_drop_all(self) -> None:
        async with self.__engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def run_async_create_all(self) -> None:
        async with self.__engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
