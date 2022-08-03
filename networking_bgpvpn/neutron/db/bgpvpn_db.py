# Copyright (c) 2015 Orange.
# All Rights Reserved.
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

from oslo_db import exception as db_exc
from oslo_log import log
from oslo_utils import uuidutils
import sqlalchemy as sa
from sqlalchemy import and_
from sqlalchemy import orm
from sqlalchemy.orm import exc

from neutron_lib.api.definitions import bgpvpn as bgpvpn_def
from neutron_lib.api.definitions import bgpvpn_routes_control as bgpvpn_rc_def
from neutron_lib.api.definitions import bgpvpn_vni as bgpvpn_vni_def
from neutron_lib.db import api as db_api
from neutron_lib.db import constants as db_const
from neutron_lib.db import model_base
from neutron_lib.db import model_query
from neutron_lib.db import standard_attr
from neutron_lib.db import utils as db_utils
from neutron_lib.plugins import directory

from neutron.db import rbac_db_models

from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from networking_bgpvpn.neutron.extensions\
    import bgpvpn_routes_control as bgpvpn_rc_ext
from networking_bgpvpn.neutron.services.common import utils

LOG = log.getLogger(__name__)


class HasProjectNotNullable(model_base.HasProject):

    project_id = sa.Column(sa.String(db_const.PROJECT_ID_FIELD_SIZE),
                           index=True,
                           nullable=False)


class BGPVPNRBAC(rbac_db_models.RBACColumns, model_base.BASEV2):
    """RBAC table for bgpvpns."""

    object_id = sa.Column(sa.String(36),
                          sa.ForeignKey('bgpvpns.id', ondelete="CASCADE"),
                          nullable=False)
    object_type = 'bgpvpn'

    @staticmethod
    def get_valid_actions():
        return (rbac_db_models.ACCESS_SHARED,)


class BGPVPNNetAssociation(standard_attr.HasStandardAttributes,
                           model_base.BASEV2, model_base.HasId,
                           HasProjectNotNullable):
    """Represents the association between a bgpvpn and a network."""
    __tablename__ = 'bgpvpn_network_associations'

    bgpvpn_id = sa.Column(sa.String(36),
                          sa.ForeignKey('bgpvpns.id', ondelete='CASCADE'),
                          nullable=False)
    network_id = sa.Column(sa.String(36),
                           sa.ForeignKey('networks.id', ondelete='CASCADE'),
                           nullable=False)
    sa.UniqueConstraint(bgpvpn_id, network_id)
    network = orm.relationship("Network",
                               backref=orm.backref('bgpvpn_associations',
                                                   cascade='all'),
                               lazy='joined',)

    # standard attributes support:
    api_collections = []
    api_sub_resources = [bgpvpn_def.NETWORK_ASSOCIATIONS]
    collection_resource_map = {bgpvpn_def.NETWORK_ASSOCIATIONS:
                               bgpvpn_def.NETWORK_ASSOCIATION}


class BGPVPNRouterAssociation(standard_attr.HasStandardAttributes,
                              model_base.BASEV2, model_base.HasId,
                              HasProjectNotNullable):
    """Represents the association between a bgpvpn and a router."""
    __tablename__ = 'bgpvpn_router_associations'

    bgpvpn_id = sa.Column(sa.String(36),
                          sa.ForeignKey('bgpvpns.id', ondelete='CASCADE'),
                          nullable=False)
    router_id = sa.Column(sa.String(36),
                          sa.ForeignKey('routers.id', ondelete='CASCADE'),
                          nullable=False)
    sa.UniqueConstraint(bgpvpn_id, router_id)
    advertise_extra_routes = sa.Column(sa.Boolean(), nullable=False,
                                       server_default=sa.true())
    router = orm.relationship("Router",
                              backref=orm.backref('bgpvpn_associations',
                                                  cascade='all'),
                              lazy='joined',)

    # standard attributes support:
    api_collections = []
    api_sub_resources = [bgpvpn_def.ROUTER_ASSOCIATIONS]
    collection_resource_map = {bgpvpn_def.ROUTER_ASSOCIATIONS:
                               bgpvpn_def.ROUTER_ASSOCIATION}


class BGPVPNPortAssociation(standard_attr.HasStandardAttributes,
                            model_base.BASEV2, model_base.HasId,
                            HasProjectNotNullable):
    """Represents the association between a bgpvpn and a port."""
    __tablename__ = 'bgpvpn_port_associations'

    bgpvpn_id = sa.Column(sa.String(36),
                          sa.ForeignKey('bgpvpns.id', ondelete='CASCADE'),
                          nullable=False)
    port_id = sa.Column(sa.String(36),
                        sa.ForeignKey('ports.id', ondelete='CASCADE'),
                        nullable=False)
    sa.UniqueConstraint(bgpvpn_id, port_id)
    advertise_fixed_ips = sa.Column(sa.Boolean(), nullable=False,
                                    server_default=sa.true())
    port = orm.relationship("Port",
                            backref=orm.backref('bgpvpn_associations',
                                                cascade='all'),
                            lazy='joined',)

    # standard attributes support:
    api_collections = []
    api_sub_resources = [bgpvpn_rc_def.PORT_ASSOCIATIONS]
    collection_resource_map = {bgpvpn_rc_def.PORT_ASSOCIATIONS:
                               bgpvpn_rc_def.PORT_ASSOCIATION}


class BGPVPN(standard_attr.HasStandardAttributes, model_base.BASEV2,
             model_base.HasId, model_base.HasProject):
    """Represents a BGPVPN Object."""
    name = sa.Column(sa.String(255))
    type = sa.Column(sa.Enum("l2", "l3",
                             name="vpn_types"),
                     nullable=False)
    route_targets = sa.Column(sa.String(255), nullable=False)
    import_targets = sa.Column(sa.String(255), nullable=True)
    export_targets = sa.Column(sa.String(255), nullable=True)
    route_distinguishers = sa.Column(sa.String(255), nullable=True)
    vni = sa.Column(sa.Integer, nullable=True)
    local_pref = sa.Column(sa.BigInteger, nullable=True)
    network_associations = orm.relationship("BGPVPNNetAssociation",
                                            backref="bgpvpn",
                                            lazy='select',
                                            cascade='all, delete-orphan')
    router_associations = orm.relationship("BGPVPNRouterAssociation",
                                           backref="bgpvpn",
                                           lazy='select',
                                           cascade='all, delete-orphan')
    port_associations = orm.relationship("BGPVPNPortAssociation",
                                         backref="bgpvpn",
                                         lazy='select',
                                         cascade='all, delete-orphan')
    rbac_entries = sa.orm.relationship(BGPVPNRBAC,
                                       backref='bgpvpn',
                                       lazy='subquery',
                                       cascade='all, delete, delete-orphan')

    # standard attributes support:
    api_collections = [bgpvpn_def.COLLECTION_NAME]
    collection_resource_map = {bgpvpn_def.COLLECTION_NAME:
                               bgpvpn_def.RESOURCE_NAME}


class BGPVPNPortAssociationRoute(model_base.BASEV2, model_base.HasId):
    """Represents an item of the 'routes' attribute of a port association."""
    __tablename__ = 'bgpvpn_port_association_routes'

    port_association_id = sa.Column(
        sa.String(length=36),
        sa.ForeignKey('bgpvpn_port_associations.id', ondelete='CASCADE'),
        nullable=False)
    type = sa.Column(sa.Enum(*bgpvpn_rc_def.ROUTE_TYPES,
                             name="bgpvpn_port_association_route_type"),
                     nullable=False)
    local_pref = sa.Column(sa.BigInteger(),
                           nullable=True)
    # prefix is NULL unless type is 'prefix'
    prefix = sa.Column(sa.String(49),
                       nullable=True)
    # bgpvpn_id is NULL unless type is 'bgpvpn'
    bgpvpn_id = sa.Column(sa.String(length=36),
                          sa.ForeignKey('bgpvpns.id', ondelete='CASCADE'),
                          nullable=True)

    port_association = orm.relationship(
        "BGPVPNPortAssociation",
        backref=orm.backref('routes',
                            cascade='all'),
        lazy='joined')
    bgpvpn = orm.relationship(
        "BGPVPN",
        backref=orm.backref("port_association_routes",
                            uselist=False,
                            lazy='select',
                            cascade='all, delete-orphan'),
        lazy='joined')


def _list_bgpvpns_result_filter_hook(query, filters):
    values = filters and filters.get('networks', [])
    if values:
        query = query.join(BGPVPNNetAssociation)
        query = query.filter(BGPVPNNetAssociation.network_id.in_(values))

    values = filters and filters.get('routers', [])
    if values:
        query = query.join(BGPVPNRouterAssociation)
        query = query.filter(BGPVPNRouterAssociation.router_id.in_(values))

    values = filters and filters.get('ports', [])
    if values:
        query = query.join(BGPVPNRouterAssociation)
        query = query.filter(BGPVPNPortAssociation.port_id.in_(values))

    return query


@db_api.CONTEXT_WRITER
def _add_port_assoc_route_db_from_dict(context, route, port_association_id):
    if route['type'] == 'prefix':
        kwargs = {'prefix': route['prefix']}
    elif route['type'] == 'bgpvpn':
        kwargs = {'bgpvpn_id': route['bgpvpn_id']}
    else:
        # not reached
        pass

    context.session.add(BGPVPNPortAssociationRoute(
        port_association_id=port_association_id,
        type=route['type'],
        local_pref=route.get('local_pref', None),
        **kwargs
    ))


def port_assoc_route_dict_from_db(route_db):
    route = {
        'type': route_db.type,
        'local_pref': route_db.local_pref
    }
    if route_db.type == 'prefix':
        route.update({'prefix': route_db.prefix})
    elif route_db.type == 'bgpvpn':
        route.update({'bgpvpn_id': route_db.bgpvpn_id})
    return route


class BGPVPNPluginDb():
    """BGPVPN service plugin database class using SQLAlchemy models."""

    def __new__(cls, *args, **kwargs):
        model_query.register_hook(
            BGPVPN,
            "bgpvpn_filter_by_resource_association",
            query_hook=None,
            filter_hook=None,
            result_filters=_list_bgpvpns_result_filter_hook)
        return super(BGPVPNPluginDb, cls).__new__(cls, *args, **kwargs)

    @db_api.CONTEXT_READER
    def _make_bgpvpn_dict(self, context, bgpvpn_db, fields=None):
        net_list = [net_assocs.network_id for net_assocs in
                    bgpvpn_db.network_associations]
        router_list = [router_assocs.router_id for router_assocs in
                       bgpvpn_db.router_associations]
        port_list = [port_assocs.port_id for port_assocs in
                     bgpvpn_db.port_associations]
        res = {
            'id': bgpvpn_db['id'],
            'tenant_id': bgpvpn_db['tenant_id'],
            'networks': net_list,
            'routers': router_list,
            'ports': port_list,
            'name': bgpvpn_db['name'],
            'type': bgpvpn_db['type'],
            'shared': self._is_shared(context, bgpvpn_db),
            'route_targets':
                utils.rtrd_str2list(bgpvpn_db['route_targets']),
            'route_distinguishers':
                utils.rtrd_str2list(bgpvpn_db['route_distinguishers']),
            'import_targets':
                utils.rtrd_str2list(bgpvpn_db['import_targets']),
            'export_targets':
                utils.rtrd_str2list(bgpvpn_db['export_targets'])
        }

        plugin = directory.get_plugin(bgpvpn_def.ALIAS)
        if utils.is_extension_supported(plugin, bgpvpn_vni_def.ALIAS):
            res[bgpvpn_vni_def.VNI] = bgpvpn_db.get(bgpvpn_vni_def.VNI)
        if utils.is_extension_supported(plugin, bgpvpn_rc_def.ALIAS):
            res[bgpvpn_rc_def.LOCAL_PREF_KEY] = bgpvpn_db.get(
                bgpvpn_rc_def.LOCAL_PREF_KEY)

        return db_utils.resource_fields(res, fields)

    @db_api.CONTEXT_READER
    def _is_shared(self, context, bgpvpn_db):
        return (context.session.query(BGPVPNRBAC).filter(
                and_(BGPVPNRBAC.object_id == bgpvpn_db['id'],
                     BGPVPNRBAC.action == rbac_db_models.ACCESS_SHARED,
                     BGPVPNRBAC.target_tenant.in_(
                         ['*', context.tenant_id]))).count() != 0)

    @db_api.CONTEXT_WRITER
    def create_bgpvpn(self, context, bgpvpn):
        rt = utils.rtrd_list2str(bgpvpn['route_targets'])
        i_rt = utils.rtrd_list2str(bgpvpn['import_targets'])
        e_rt = utils.rtrd_list2str(bgpvpn['export_targets'])
        rd = utils.rtrd_list2str(bgpvpn.get('route_distinguishers', ''))

        with db_api.CONTEXT_WRITER.using(context):
            bgpvpn_db = BGPVPN(
                id=uuidutils.generate_uuid(),
                tenant_id=bgpvpn['tenant_id'],
                name=bgpvpn['name'],
                type=bgpvpn['type'],
                route_targets=rt,
                import_targets=i_rt,
                export_targets=e_rt,
                route_distinguishers=rd,
                vni=bgpvpn.get(bgpvpn_vni_def.VNI),
                local_pref=bgpvpn.get(bgpvpn_rc_def.LOCAL_PREF_KEY),
            )
            context.session.add(bgpvpn_db)

        return self._make_bgpvpn_dict(context, bgpvpn_db)

    @db_api.CONTEXT_READER
    def get_bgpvpns(self, context, filters=None, fields=None):
        objs = model_query.get_collection(
            context, BGPVPN, None,
            filters=filters, fields=fields)
        return [self._make_bgpvpn_dict(
                context, obj, fields=fields) for obj in objs]

    @db_api.CONTEXT_READER
    def _get_bgpvpn(self, context, id):
        try:
            return model_query.get_by_id(context, BGPVPN, id)
        except exc.NoResultFound:
            raise bgpvpn_ext.BGPVPNNotFound(id=id)

    @db_api.CONTEXT_READER
    def get_bgpvpn(self, context, id, fields=None):
        bgpvpn_db = self._get_bgpvpn(context, id)
        return self._make_bgpvpn_dict(context, bgpvpn_db, fields)

    @db_api.CONTEXT_WRITER
    def update_bgpvpn(self, context, id, bgpvpn):
        bgpvpn_db = self._get_bgpvpn(context, id)
        if bgpvpn:
            # Format Route Target lists to string
            if 'route_targets' in bgpvpn:
                rt = utils.rtrd_list2str(bgpvpn['route_targets'])
                bgpvpn['route_targets'] = rt
            if 'import_targets' in bgpvpn:
                i_rt = utils.rtrd_list2str(bgpvpn['import_targets'])
                bgpvpn['import_targets'] = i_rt
            if 'export_targets' in bgpvpn:
                e_rt = utils.rtrd_list2str(bgpvpn['export_targets'])
                bgpvpn['export_targets'] = e_rt
            if 'route_distinguishers' in bgpvpn:
                rd = utils.rtrd_list2str(bgpvpn['route_distinguishers'])
                bgpvpn['route_distinguishers'] = rd
            bgpvpn_db.update(bgpvpn)
        return self._make_bgpvpn_dict(context, bgpvpn_db)

    @db_api.CONTEXT_WRITER
    def delete_bgpvpn(self, context, id):
        bgpvpn_db = self._get_bgpvpn(context, id)
        bgpvpn = self._make_bgpvpn_dict(context, bgpvpn_db)
        context.session.delete(bgpvpn_db)
        return bgpvpn

    @db_api.CONTEXT_READER
    def _make_net_assoc_dict(self, net_assoc_db, fields=None):
        res = {'id': net_assoc_db['id'],
               'tenant_id': net_assoc_db['tenant_id'],
               'bgpvpn_id': net_assoc_db['bgpvpn_id'],
               'network_id': net_assoc_db['network_id']}
        return db_utils.resource_fields(res, fields)

    @db_api.CONTEXT_READER
    def _get_net_assoc(self, context, assoc_id, bgpvpn_id):
        try:
            query = model_query.query_with_hooks(context, BGPVPNNetAssociation)
            return query.filter(BGPVPNNetAssociation.id == assoc_id,
                                BGPVPNNetAssociation.bgpvpn_id == bgpvpn_id
                                ).one()
        except exc.NoResultFound:
            raise bgpvpn_ext.BGPVPNNetAssocNotFound(id=assoc_id,
                                                    bgpvpn_id=bgpvpn_id)

    def create_net_assoc(self, context, bgpvpn_id, net_assoc):
        try:
            with db_api.CONTEXT_WRITER.using(context):
                net_assoc_db = BGPVPNNetAssociation(
                    tenant_id=net_assoc['tenant_id'],
                    bgpvpn_id=bgpvpn_id,
                    network_id=net_assoc['network_id'])
                context.session.add(net_assoc_db)
            return self._make_net_assoc_dict(net_assoc_db)
        except db_exc.DBDuplicateEntry:
            LOG.warning("network %(net_id)s is already associated to "
                        "BGPVPN %(bgpvpn_id)s",
                        {'net_id': net_assoc['network_id'],
                         'bgpvpn_id': bgpvpn_id})
            raise bgpvpn_ext.BGPVPNNetAssocAlreadyExists(
                bgpvpn_id=bgpvpn_id, net_id=net_assoc['network_id'])

    @db_api.CONTEXT_READER
    def get_net_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        net_assoc_db = self._get_net_assoc(context, assoc_id, bgpvpn_id)
        return self._make_net_assoc_dict(net_assoc_db, fields)

    @db_api.CONTEXT_READER
    def get_net_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        if not filters:
            filters = {}
        filters['bgpvpn_id'] = [bgpvpn_id]
        return model_query.get_collection(
            context, BGPVPNNetAssociation,
            self._make_net_assoc_dict,
            filters, fields)

    @db_api.CONTEXT_WRITER
    def delete_net_assoc(self, context, assoc_id, bgpvpn_id):
        LOG.info("deleting network association %(id)s for "
                 "BGPVPN %(bgpvpn)s", {'id': assoc_id,
                                       'bgpvpn': bgpvpn_id})
        net_assoc_db = self._get_net_assoc(context, assoc_id, bgpvpn_id)
        net_assoc = self._make_net_assoc_dict(net_assoc_db)
        context.session.delete(net_assoc_db)
        return net_assoc

    def _make_router_assoc_dict(self, router_assoc_db, fields=None):
        res = {'id': router_assoc_db['id'],
               'tenant_id': router_assoc_db['tenant_id'],
               'bgpvpn_id': router_assoc_db['bgpvpn_id'],
               'router_id': router_assoc_db['router_id'],
               'advertise_extra_routes': router_assoc_db[
                   'advertise_extra_routes']
               }
        return db_utils.resource_fields(res, fields)

    @db_api.CONTEXT_READER
    def _get_router_assoc(self, context, assoc_id, bgpvpn_id):
        try:
            query = model_query.query_with_hooks(
                context, BGPVPNRouterAssociation)
            return query.filter(BGPVPNRouterAssociation.id == assoc_id,
                                BGPVPNRouterAssociation.bgpvpn_id == bgpvpn_id
                                ).one()
        except exc.NoResultFound:
            raise bgpvpn_ext.BGPVPNRouterAssocNotFound(id=assoc_id,
                                                       bgpvpn_id=bgpvpn_id)

    @db_api.CONTEXT_WRITER
    def create_router_assoc(self, context, bgpvpn_id, router_association):
        router_id = router_association['router_id']
        try:
            router_assoc_db = BGPVPNRouterAssociation(
                tenant_id=router_association['tenant_id'],
                bgpvpn_id=bgpvpn_id,
                router_id=router_id)
            context.session.add(router_assoc_db)
            context.session.flush()
            return self._make_router_assoc_dict(router_assoc_db)
        except db_exc.DBDuplicateEntry:
            LOG.warning("router %(router_id)s is already associated to "
                        "BGPVPN %(bgpvpn_id)s",
                        {'router_id': router_id,
                         'bgpvpn_id': bgpvpn_id})
            raise bgpvpn_ext.BGPVPNRouterAssocAlreadyExists(
                bgpvpn_id=bgpvpn_id, router_id=router_association['router_id'])

    @db_api.CONTEXT_READER
    def get_router_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        router_assoc_db = self._get_router_assoc(context, assoc_id, bgpvpn_id)
        return self._make_router_assoc_dict(router_assoc_db, fields)

    @db_api.CONTEXT_READER
    def get_router_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        if not filters:
            filters = {}
        filters['bgpvpn_id'] = [bgpvpn_id]
        return model_query.get_collection(
            context, BGPVPNRouterAssociation,
            self._make_router_assoc_dict,
            filters, fields)

    @db_api.CONTEXT_WRITER
    def update_router_assoc(self, context, assoc_id, bgpvpn_id, router_assoc):
        router_assoc_db = self._get_router_assoc(context,
                                                 assoc_id, bgpvpn_id)
        router_assoc_db.update(router_assoc)
        return self._make_router_assoc_dict(router_assoc_db)

    @db_api.CONTEXT_WRITER
    def delete_router_assoc(self, context, assoc_id, bgpvpn_id):
        LOG.info("deleting router association %(id)s for "
                 "BGPVPN %(bgpvpn)s",
                 {'id': assoc_id, 'bgpvpn': bgpvpn_id})
        router_assoc_db = self._get_router_assoc(context, assoc_id,
                                                 bgpvpn_id)
        router_assoc = self._make_router_assoc_dict(router_assoc_db)
        context.session.delete(router_assoc_db)
        return router_assoc

    @db_api.CONTEXT_READER
    def _make_port_assoc_dict(self, port_assoc_db, fields=None):
        routes = [port_assoc_route_dict_from_db(r)
                  for r in port_assoc_db['routes']]
        res = {'id': port_assoc_db['id'],
               'tenant_id': port_assoc_db['tenant_id'],
               'bgpvpn_id': port_assoc_db['bgpvpn_id'],
               'port_id': port_assoc_db['port_id'],
               'advertise_fixed_ips': port_assoc_db['advertise_fixed_ips'],
               'routes': routes}
        return db_utils.resource_fields(res, fields)

    @db_api.CONTEXT_READER
    def _get_port_assoc(self, context, assoc_id, bgpvpn_id):
        try:
            query = model_query.query_with_hooks(
                context, BGPVPNPortAssociation)
            return query.filter(BGPVPNPortAssociation.id == assoc_id,
                                BGPVPNPortAssociation.bgpvpn_id == bgpvpn_id
                                ).one()
        except exc.NoResultFound:
            raise bgpvpn_rc_ext.BGPVPNPortAssocNotFound(id=assoc_id,
                                                        bgpvpn_id=bgpvpn_id)

    def create_port_assoc(self, context, bgpvpn_id, port_association):
        port_id = port_association['port_id']
        advertise_fixed_ips = port_association['advertise_fixed_ips']
        try:
            with db_api.CONTEXT_WRITER.using(context):
                port_assoc_db = BGPVPNPortAssociation(
                    tenant_id=port_association['tenant_id'],
                    bgpvpn_id=bgpvpn_id,
                    port_id=port_id,
                    advertise_fixed_ips=advertise_fixed_ips)
                context.session.add(port_assoc_db)
        except db_exc.DBDuplicateEntry:
            LOG.warning(("port %(port_id)s is already associated to "
                         "BGPVPN %(bgpvpn_id)s"),
                        {'port_id': port_id,
                         'bgpvpn_id': bgpvpn_id})
            raise bgpvpn_rc_ext.BGPVPNPortAssocAlreadyExists(
                bgpvpn_id=bgpvpn_id, port_id=port_association['port_id'])

        for route in port_association['routes']:
            _add_port_assoc_route_db_from_dict(
                context, route, port_assoc_db.id)
        return self._make_port_assoc_dict(port_assoc_db)

    @db_api.CONTEXT_READER
    def get_port_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        port_assoc_db = self._get_port_assoc(context, assoc_id, bgpvpn_id)
        return self._make_port_assoc_dict(port_assoc_db, fields)

    @db_api.CONTEXT_READER
    def get_port_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        if not filters:
            filters = {}
        filters['bgpvpn_id'] = [bgpvpn_id]
        return model_query.get_collection(
            context, BGPVPNPortAssociation,
            self._make_port_assoc_dict,
            filters, fields)

    def update_port_assoc(self, context, assoc_id, bgpvpn_id, port_assoc):
        with db_api.CONTEXT_WRITER.using(context):
            port_assoc_db = self._get_port_assoc(context, assoc_id, bgpvpn_id)
            for route_db in port_assoc_db.routes:
                context.session.delete(route_db)
            for route in port_assoc.pop('routes', []):
                _add_port_assoc_route_db_from_dict(context, route, assoc_id)
            port_assoc_db.update(port_assoc)
        context.session.refresh(port_assoc_db)
        return self._make_port_assoc_dict(port_assoc_db)

    @db_api.CONTEXT_WRITER
    def delete_port_assoc(self, context, assoc_id, bgpvpn_id):
        LOG.info(("deleting port association %(id)s for "
                  "BGPVPN %(bgpvpn)s"),
                 {'id': assoc_id, 'bgpvpn': bgpvpn_id})
        port_assoc_db = self._get_port_assoc(context, assoc_id,
                                             bgpvpn_id)
        port_assoc = self._make_port_assoc_dict(port_assoc_db)
        context.session.delete(port_assoc_db)
        return port_assoc
