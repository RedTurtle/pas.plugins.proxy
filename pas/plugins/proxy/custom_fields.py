# -*- coding: utf-8 -*-

from zope import schema
from zope.interface import Interface, implements

from z3c.form.object import registerFactoryAdapter
from plone.registry.field import PersistentField
from pas.plugins.proxy import pppMessageFactory as _


class IProxyValueField(Interface):
    delegator = schema.TextLine(
            title=_("ppp_delegator_label", default=u"Delegator user"),
            description=_("ppp_delegator_help",
                          default=u'Select which user should delegate his roles.'),
            required=True,
    )
    delegated = schema.TextLine(
            title=_("ppp_delegated_label", default=u"Delegated user"),
            description=_("ppp_delegated_help",
                          default=u'Select which user should acquire delegator roles.'),
            required=True,
    )


class ProxyValueField(object):
    implements(IProxyValueField)


class PersistentObject(PersistentField, schema.Object):
    pass

registerFactoryAdapter(IProxyValueField, ProxyValueField)
