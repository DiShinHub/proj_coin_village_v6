from sqlalchemy import select, and_, func, text, case
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update

from app.helper.sql_session_helper import SqlSessionHelper
from app.model.entity.mbr_member_auth_jwt_entity import MbrMemberAuthJwtEntity
from app.model.entity.mbr_member_entity import MbrMemberEntity, MbrMemberEnums
from app.model.entity.mbr_member_role_entity import MbrMemberRoleEntity

import datetime


class MbrMemberDao:
    __get_scoped_session = None

    def __init__(self, get_scoped_session):
        self.__get_scoped_session = get_scoped_session

    async def add_member(self, mbr_member: MbrMemberEntity) -> list[MbrMemberEntity]:
        stmt = (
            insert(MbrMemberEntity)
            .values(
                member_id=mbr_member.member_id,
                member_password=mbr_member.member_password,
                member_first_name=mbr_member.member_first_name,
                member_last_name=mbr_member.member_last_name,
                member_email=mbr_member.member_email,
                member_phone=mbr_member.member_phone,
                member_type_cd=mbr_member.member_type_cd,
                member_status_cd=mbr_member.member_status_cd,
                reg_dt=datetime.datetime.now(),
                reg_member_seq=mbr_member.reg_member_seq,
                mod_dt=datetime.datetime.now(),
                mod_member_seq=mbr_member.reg_member_seq,
            )
            .returning(MbrMemberEntity.member_seq)
        )
        result = await SqlSessionHelper.execute(
            session=self.__get_scoped_session()(),
            stmt=stmt
        )
        return [MbrMemberEntity(**(row._mapping)) for row in result.fetchall()]

    async def add_member_auth_jwt(self, mbr_member_auth_jwt: MbrMemberAuthJwtEntity) -> list[MbrMemberAuthJwtEntity]:
        stmt = (
            insert(MbrMemberAuthJwtEntity)
            .values(
                member_seq=mbr_member_auth_jwt.member_seq,
                member_id=mbr_member_auth_jwt.member_id,
                access_token=mbr_member_auth_jwt.access_token,
                refresh_token=mbr_member_auth_jwt.refresh_token,
                expiration_dt=mbr_member_auth_jwt.expiration_dt,
                reg_dt=func.now(),
                reg_member_seq=mbr_member_auth_jwt.reg_member_seq,
                mod_dt=func.now(),
                mod_member_seq=mbr_member_auth_jwt.reg_member_seq
            )
            .on_conflict_do_update(
                index_elements=["member_id"],
                set_={
                    "access_token": mbr_member_auth_jwt.access_token,
                    "refresh_token": mbr_member_auth_jwt.refresh_token,
                    "expiration_dt": mbr_member_auth_jwt.expiration_dt,
                    "mod_dt": func.now(),
                    "mod_member_seq": mbr_member_auth_jwt.reg_member_seq
                }
            )
            .returning(MbrMemberAuthJwtEntity.member_seq)
        )
        result = await SqlSessionHelper.execute(
            session=self.__get_scoped_session()(),
            stmt=stmt
        )
        return [MbrMemberAuthJwtEntity(**(row._mapping)) for row in result.fetchall()]
    
    async def get_member_for_login(
            self,
            member_id: str
    ) -> MbrMemberEntity | None:
        stmt = (
            select(
                MbrMemberEntity.member_seq,
                MbrMemberEntity.member_id,
                MbrMemberEntity.member_password,
                MbrMemberEntity.member_type_cd,
                MbrMemberEntity.member_status_cd,
                MbrMemberEntity.reg_member_seq,
            )
            .where(
                and_(
                    MbrMemberEntity.member_id == member_id
                )
            )
        )
        result = await SqlSessionHelper.execute(
            session=self.__get_scoped_session()(),
            stmt=stmt
        )
        fetch_result = result.fetchone()
        return MbrMemberEntity(**(fetch_result._mapping)) if fetch_result else None
    