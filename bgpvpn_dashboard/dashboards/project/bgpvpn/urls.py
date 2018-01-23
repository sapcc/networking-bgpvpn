# Copyright (c) 2016 Orange.
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

from django.conf.urls import include
from django.conf.urls import url

from bgpvpn_dashboard.dashboards.project.bgpvpn.network_associations import \
    urls as network_associations_urls
from bgpvpn_dashboard.dashboards.project.bgpvpn.network_associations import \
    views as network_associations_views
from bgpvpn_dashboard.dashboards.project.bgpvpn import views as bgpvpn_views

BGPVPN = r'^(?P<bgpvpn_id>[^/]+)/%s$'

urlpatterns = [
    url(r'^$', bgpvpn_views.IndexView.as_view(), name='index'),
    url(BGPVPN % 'edit', bgpvpn_views.EditDataView.as_view(), name='edit'),
    url(BGPVPN % 'update-associations',
        bgpvpn_views.UpdateAssociationsView.as_view(),
        name='update-associations'),
    url(BGPVPN % 'create-network-association',
        bgpvpn_views.CreateNetworkAssociationView.as_view(),
        name='create-network-association'),
    url(r'^(?P<bgpvpn_id>[^/]+)/detail/$',
        bgpvpn_views.DetailProjectView.as_view(), name='detail'),
    url(r'^(?P<bgpvpn_id>[^/]+)/network_assos/'
        r'(?P<network__association_id>[^/]+)/'
        r'detail\?tab=bgpvpns__network__associations_tab$',
        network_associations_views.DetailView.as_view(),
        name='network_associations_tab'),
    url(r'^network_assos/', include(network_associations_urls,
                                    namespace='network_assos')),
]
