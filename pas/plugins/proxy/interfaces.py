# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope import schema
from pas.plugins.proxy import pppMessageFactory as _
from pas.plugins.proxy.custom_fields import IProxyValueField, PersistentObject


class IPasPluginsProxyLayer(Interface):
    """ Browser layer interface """


class IProxyRolesSettings(Interface):
    """Settings used in the control panel for sitesearch: General settings
    """

    proxy_roles = schema.Tuple(
            title=_(u'Proxy roles'),
            description=_('help_proxy_roles',
                          default=u""),
            value_type=PersistentObject(IProxyValueField, title=_(u"Proxy")),
            required=False,
            default=(),
            missing_value=()
        )
