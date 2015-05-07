# -*- coding: utf-8 -*-

from pas.plugins.proxy import pppMessageFactory as _
from plone import api
from plone.memoize import view
from plone.registry.field import PersistentField
from z3c.form import widget
from z3c.form.browser.multi import MultiWidget
from z3c.form.interfaces import IFieldWidget, IFormLayer
from z3c.form.interfaces import IMultiWidget
from z3c.form.interfaces import INPUT_MODE, IErrorViewSnippet
from z3c.form.object import registerFactoryAdapter
from zope import schema
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface, implements
from zope.interface import Invalid
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory
from zope.schema.interfaces import IField
from zope.schema.interfaces import IMinMaxLen


class IProxyUsersMultiWidget(IMultiWidget):
    """Marker interface
    """


@implementer(IProxyUsersMultiWidget)
class ProxyUsersMultiWidget(MultiWidget):
    """Custom multiwidget that filters available values"""

    @property
    @view.memoize
    def current_user(self):
        return api.user.get_current()

    def canManageEntry(self, mapping):
        """
        Check if current user can set the given mapping.
        """
        user = self.current_user
        portal = api.portal.get()
        if user.checkPermission('pas.plugins.proxy: Manage proxy roles',
                                portal):
            return True
        if user.getProperty('id') == mapping.get('delegator'):
            return True
        return False

    def updateWidgets(self):
        """Setup internal widgets based on the value_type for each value item.
        """
        oldLen = len(self.widgets)
        # Ensure at least min_length widgets are shown
        if (IMinMaxLen.providedBy(self.field) and
            self.mode == INPUT_MODE and self.allowAdding and
            oldLen < self.field.min_length):
            oldLen = self.field.min_length
        self.widgets = []
        self.key_widgets = []
        keys = set()
        idx = 0
        if self.value:
            if self.is_dict:
                # mainly sorting for testing reasons
                items = self.value
            else:
                items = zip([None] * len(self.value), self.value)
            for key, v in items:
                if not self.canManageEntry(v):
                    continue
                widget = self.getWidget(idx)
                self.applyValue(widget, v)
                self.widgets.append(widget)

                if self.is_dict:
                    # This is needed, since sequence widgets (such as for
                    # choices) return lists of values.
                    hash_key = key if not isinstance(key, list) else tuple(key)
                    widget = self.getWidget(idx, "key", "key_type")
                    self.applyValue(widget, key)
                    if hash_key in keys and widget.error is None:
                        error = Invalid(u'Duplicate key')
                        view = getMultiAdapter(
                            (error, self.request, widget, widget.field,
                             self.form, self.context),
                            IErrorViewSnippet)
                        view.update()
                        widget.error = view
                    self.key_widgets.append(widget)
                    keys.add(hash_key)
                else:
                    #makes the template easier to have this the same length
                    self.key_widgets.append(None)
                idx += 1
        missing = oldLen - len(self.widgets)
        if missing > 0:
            # add previous existing new added widgtes
            for i in range(missing):
                widget = self.getWidget(idx)
                self.widgets.append(widget)
                if self.is_dict:
                    widget = self.getWidget(idx, "key", "key_type")
                    self.key_widgets.append(widget)
                else:
                    self.key_widgets.append(None)
                idx += 1
        self._widgets_updated = True


@adapter(IField, IFormLayer)
@implementer(IFieldWidget)
def ProxyUsersMultiFieldWidget(field, request):
    """IFieldWidget factory for MultiWidget."""
    return widget.FieldWidget(field, ProxyUsersMultiWidget(request))


@provider(IContextAwareDefaultFactory)
def default_delegator(context):
    """
    If the user can't manage proxy roles, return his username as default
    """
    user = api.user.get_current()
    portal = api.portal.get()
    if user.checkPermission('pas.plugins.proxy: Manage proxy roles',
                            portal):
        return ""
    return user.getProperty('id')


class IProxyValueField(Interface):
    delegator = schema.ASCIILine(
            title=_("ppp_delegator_label", default=u"Delegator user"),
            description=_("ppp_delegator_help",
                          default=u'Select which user should delegate his roles.'),
            required=True,
            defaultFactory=default_delegator,
    )
    delegated = schema.ASCIILine(
            title=_("ppp_delegated_label", default=u"Delegated user"),
            description=_("ppp_delegated_help",
                          default=u'Select which user should acquire delegator roles.'),
            required=True,
    )


class ProxyValueField(object):
    implements(IProxyValueField)
    
    def __init__(self, delegator=None, delegated=None):
        self.delegator = delegator
        self.delegated = delegated


class PersistentObject(PersistentField, schema.Object):
    pass


registerFactoryAdapter(IProxyValueField, ProxyValueField)
