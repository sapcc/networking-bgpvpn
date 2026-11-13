# Copyright 2022 <PUT YOUR NAME/COMPANY HERE>
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

"""rename target_tenant

Revision ID: 1aa861614c9e
Revises: 3812c14fde5c
Create Date: 2022-11-30 18:45:39.638130

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1aa861614c9e'
down_revision = '3812c14fde5c'


def upgrade():
    op.alter_column(
        table_name='bgpvpnrbacs',
        column_name='target_tenant',
        new_column_name='target_project',
        existing_type=sa.String(length=255),
        existing_nullable=False)
