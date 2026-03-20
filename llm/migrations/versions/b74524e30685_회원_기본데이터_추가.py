"""회원 기본데이터 추가

Revision ID: b74524e30685
Revises: 7a075c07f34b
Create Date: 2022-12-28 01:37:50.915807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b74524e30685"
down_revision = "7a075c07f34b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT 
          INTO  mbr_member
             (
                member_seq
                , member_id
                , member_password
                , member_type_cd
                , member_status_cd
                , member_name
                , reg_dt
                , reg_member_seq
                , mod_dt
                , mod_member_seq
             )
        VALUES
             (
                1
                , 'admin@aizen.co'
                , '$2b$12$lgC1XPpUsjm6vW/529XGi.xPh1hBc1AJbY5Hm/p1FhCrUC4rc16Y6'
                , 'MBT111'
                , 'MBS111'
                , '관리자'
                , CURRENT_TIMESTAMP
                , 0
                , CURRENT_TIMESTAMP
                , 0
             )
    """)


def downgrade() -> None:
    op.execute("""
        DELETE 
          FROM  mbr_member
         WHERE  1 = 1
           AND  member_seq = 1
           AND  member_id = 'admin@aizen.co'
           AND  member_type_cd = 'MBT111'
    """)
