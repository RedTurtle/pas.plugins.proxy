# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope import schema
from pas.plugins.proxy import pppMessageFactory as _
from pas.plugins.proxy.custom_fields import IProxyValueField, PersistentObject
from plone.directives import form
from  pas.plugins.proxy.custom_fields import ProxyUsersMultiFieldWidget


class IPasPluginsProxyLayer(Interface):
    """ Browser layer interface """


class IProxyRolesSettings(Interface):
    """Settings used in the control panel for sitesearch: General settings
    """

    version_number = schema.Int(
        title=_('ppp_version_number',
                u'Proxy roles'),
        required=False,)

    form.widget(proxy_roles=ProxyUsersMultiFieldWidget)
    proxy_roles = schema.Tuple(
            title=_('ppp_proxy_roles',
                    u'Proxy roles'),
            description=_('help_proxy_roles',
                          default=u""),
            value_type=PersistentObject(IProxyValueField, title=_('ppp_proxy',
                                                                   u"Proxy")),
            required=False,
            default=(),
            missing_value=()
        )
