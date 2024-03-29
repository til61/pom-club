"""empty message

Revision ID: 7f4ce7450ff6
Revises: 
Create Date: 2023-05-24 16:47:37.827059

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f4ce7450ff6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('images',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('image_link', sa.Text(), nullable=False),
    sa.Column('uploader_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.Column('comment_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
    sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.drop_constraint('comments_post_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('comments_parent_id_fkey1', type_='foreignkey')
        batch_op.create_foreign_key(None, 'posts', ['post_id'], ['id'])
        batch_op.drop_column('image_link')

    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_column('image_link')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_link', sa.TEXT(), autoincrement=False, nullable=True))

    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_link', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('comments_parent_id_fkey1', 'comments', ['parent_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('comments_post_id_fkey', 'posts', ['post_id'], ['id'], ondelete='CASCADE')

    op.drop_table('images')
    # ### end Alembic commands ###
