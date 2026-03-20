import asyncio
from pathlib import Path

from app.config.database_config.database_config_repository import get_scoped_session, get_session
from app.config.database_config.database_config_runner import DatabaseConfigRunner
from app.config.logging_config.logging_config_runner import LoggingConfigRunner
from app.dao.mbr_member_dao import MbrMemberDao
from app.model.entity.mbr_member_entity import MbrMemberEnums
from app.tool.log_tool import LogTool


class TestMbrMemberDao:
    __logger = LogTool.get_logger(__qualname__)

    __get_session = None
    __get_scoped_session = None

    def __init__(self, get_session, get_scoped_session):
        logging_config_runner = LoggingConfigRunner(
            _is_singleton=True,
            logging_properties_location=Path("../../properties/logging_properties.yaml"),
            logging_properties_local_location=Path("../../properties/logging_properties.yaml.local"),
        )
        logging_config_runner.run()
        self.__get_session = get_session
        self.__get_scoped_session = get_scoped_session

    async def __call__(self, *args, **kwargs):
        await self.config()
        await self.test()
        await self.wrap_up()

    async def config(self):
        database_config_runner = DatabaseConfigRunner(
            _is_singleton=True,
            database_properties_location=Path("../../properties/database_properties.yaml"),
            database_properties_local_location=Path("../../properties/database_properties.yaml.local"),
        )
        database_config_runner.run(is_async=True, engine_echo=True)

    async def test(self):
        mbr_member_dao = MbrMemberDao(get_scoped_session=self.__get_scoped_session)
        await self.test_get_member_by_id(mbr_member_dao)
        await self.test_get_member_for_login(mbr_member_dao)
        await self.test_get_member_roles(mbr_member_dao)

    async def test_get_member_by_id(self, mbr_member_dao: MbrMemberDao):
        query_get_member_by_id = await mbr_member_dao.get_member_by_id("admin@aizen.co")
        self.__logger.debug(query_get_member_by_id[0].member_name)

    async def test_get_member_for_login(self, mbr_member_dao: MbrMemberDao):
        query_get_member_for_login = await mbr_member_dao.get_member_for_login("admin@aizen.co",
                                                                               MbrMemberEnums.MemberType.ADMIN)
        self.__logger.debug(query_get_member_for_login.member_id)

    async def test_get_member_roles(self, mbr_member_dao: MbrMemberDao):
        query_get_member_role_list = await mbr_member_dao.get_member_role_list(1)
        self.__logger.debug(query_get_member_role_list)

    async def wrap_up(self):
        await self.__get_session().rollback()
        await self.__get_scoped_session().close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TestMbrMemberDao(get_session=get_session, get_scoped_session=get_scoped_session)())
