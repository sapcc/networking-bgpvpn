# Copyright 2021 Cloudification GmbH. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""Add rbac support for bgpvpns

Revision ID: 3812c14fde5c
Revises: 9d7f1ae5fa56
Create Date: 2021-07-27 23:03:04.354967

"""

# revision identifiers, used by Alembic.
revision = '3812c14fde5c'
down_revision = '9d7f1ae5fa56'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'bgpvpnrbacs', sa.MetaData(),
        sa.Column('project_id', sa.String(length=255), nullable=True,
                  index=True),
        sa.Column('id', sa.String(length=36), nullable=False,
                  primary_key=True),
        sa.Column('target_tenant', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('object_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['object_id'], ['bgpvpns.id'],
                                ondelete='CASCADE'),
        sa.UniqueConstraint('target_tenant', 'object_id', 'action',
                            name='uniq_bgpvpns_rbacs0'
                                 'target_tenant0object_id0action')
    )
