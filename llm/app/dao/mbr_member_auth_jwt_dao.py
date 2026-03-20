from sqlalchemy import select, and_

from app.helper.sql_session_helper import SqlSessionHelper
from app.model.entity.mbr_member_auth_jwt_entity import MbrMemberAuthJwtEntity
from app.model.entity.mbr_member_entity import MbrMemberEntity


class MbrMemberAuthJwtDao:
    ___get_scoped_session = None

    def __init__(self, get_scoped_session):
        self.__get_scoped_session = get_scoped_session

    async def get_member_auth_jwt(
            self,
            member_seq: int,
            member_id: str,
    ) -> MbrMemberAuthJwtEntity | None:
        stmt = (
            select(
                MbrMemberAuthJwtEntity.member_auth_jwt_seq,
                MbrMemberAuthJwtEntity.member_seq,
                MbrMemberAuthJwtEntity.member_id,
                MbrMemberAuthJwtEntity.access_token,
                MbrMemberAuthJwtEntity.refresh_token,
                MbrMemberAuthJwtEntity.expiration_dt
            )
            .where(
                and_(
                    MbrMemberAuthJwtEntity.member_seq == member_seq,
                    MbrMemberAuthJwtEntity.member_id == member_id,
                )
            )
        )
        result = await SqlSessionHelper.execute(
            session=self.__get_scoped_session()(),
            stmt=stmt,
        )
        fetch_result = result.fetchone()
        return MbrMemberAuthJwtEntity(**(fetch_result._mapping)) if fetch_result else None
