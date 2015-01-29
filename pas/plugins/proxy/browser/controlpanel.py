# -*- coding: utf-8 -*-
from pas.plugins.proxy import pppMessageFactory as _
from pas.plugins.proxy.custom_fields import ProxyValueField
from pas.plugins.proxy.interfaces import IProxyRolesSettings
from plone import api
from plone.app.registry.browser import controlpanel
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form.form import applyChanges
from z3c.form.interfaces import WidgetActionExecutionError
from zope.interface import Invalid


class ProxyRolesSettingsEditForm(controlpanel.RegistryEditForm):
    """ Proxy roles settings form """
    schema = IProxyRolesSettings
    id = "ProxyRolesSettingsEditForm"
    label = _(u"Proxy Roles Settings")
    description = _(u"help_proxyroles_settings_editform",
                    default=u"Set proxy roles.")

    def validate_values(self, data):
        """
        If there are duplicate entries, return an error.
        If an username doesn't exist, return an error.
        If the current user tries to delegate different users, and doesn't have
        the right permission, return an error.
        """
        proxy_roles = [(getattr(x, 'delegator', ''),
                        getattr(x, 'delegated', '')) for x in data.get('proxy_roles', [])]
        if len(proxy_roles) != len(set(proxy_roles)):
            return _(u"Do not duplicate entries.")
        for proxy_role in proxy_roles:
            delegator = proxy_role[0]
            delegated = proxy_role[1]
            user = api.user.get_current()
            if not api.user.get(username=delegated) or not api.user.get(username=delegator):
                return _(u"You should select an existend username.")
            if not user.checkPermission(
                'pas.plugins.proxy: Manage proxy roles',
                self.context) and user.getProperty('id') != delegator:
                return _(u"You cannot delegate other users.")

        return None

    @button.buttonAndHandler(_('Save'), name='save')
    def handleSave(self, action):
        """"""
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        #additional validation
        proxy_validation_msg = self.validate_values(data)
        if proxy_validation_msg:
            raise WidgetActionExecutionError('proxy_roles',
                Invalid(proxy_validation_msg))
        self.applyChanges(data)
        #reindex allowedRolesAndUsers index, to update the permissions in catalog
        catalog = api.portal.get_tool(name='portal_catalog')
        catalog.reindexIndex('allowedRolesAndUsers', self.request)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"),
                                                      "info")
        self.context.REQUEST.RESPONSE.redirect("@@proxy-roles-settings")

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled"),
                                                      "info")
        self.request.response.redirect("%s/%s" % (self.context.absolute_url(),
                                                  self.control_panel_view))

    def save_delegated_changes(self, registry, user, data):
        """
        If the user can't manage all delegations, save them manually
        """
        username = user.getProperty('id')
        #we remove entries where the delegator is the current user.
        #His delegations will be added in the for loop
        clean_registry_values = [x for x in registry.proxy_roles if x.delegator != username]
        for entry in data.get('proxy_roles', []):
            new_value = ProxyValueField()
            new_value.delegator = getattr(entry, 'delegator', '')
            new_value.delegated = getattr(entry, 'delegated', '')
            clean_registry_values.append(new_value)
        registry.proxy_roles = tuple(clean_registry_values)
        return True

    def applyChanges(self, data):
        content = self.getContent()
        user = api.user.get_current()
        if user.checkPermission('pas.plugins.proxy: Manage proxy roles',
                                    self.context):
            #if the user can manage all the roles, do the usual save
            changes = applyChanges(self, content, data)
        else:
            changes = self.save_delegated_changes(registry=content,
                                                  user=user,
                                                  data=data)
        return changes


class ProxyRolesControlPanel(controlpanel.ControlPanelFormWrapper):
    """Sitesearch settings control panel.
    """
    form = ProxyRolesSettingsEditForm
