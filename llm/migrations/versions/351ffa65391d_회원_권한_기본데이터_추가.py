"""회원 권한 기본데이터 추가

Revision ID: 351ffa65391d
Revises: 44c22b62a683
Create Date: 2023-09-11 20:36:43.067659

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "351ffa65391d"
down_revision = "44c22b62a683"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT 
          INTO  mbr_member_role
             (
                member_role_seq
                , member_role
                , reg_dt
                , reg_member_seq
                , mod_dt
                , mod_member_seq
             )
        VALUES
             (
                1
                , 'ROLE_ADMIN'
                , CURRENT_TIMESTAMP
                , 0
                , CURRENT_TIMESTAMP
                , 0
            )
        """)
    op.execute("""
            INSERT 
              INTO  mbr_member_role_map
                 (
                    member_role_map_seq
                    , member_role_seq
                    , member_seq
                 )
            VALUES
                 (
                    1
                    , 1
                    , 1
                )
            """)


def downgrade() -> None:
    op.execute("""
            DELETE
              FROM  mbr_member_role 
             WHERE  1 = 1
               AND  member_role_seq = 1
               AND  member_role = 'ROLE_ADMIN'
        """)
    op.execute("""
            DELETE
              FROM  mbr_member_role_map
             WHERE  1 = 1
               AND  member_role_map_seq = 1
               AND  member_role_seq = 1
               AND  member_seq = 1
            """)
