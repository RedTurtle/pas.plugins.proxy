# -*- coding: utf-8 -*-

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.User import UnrestrictedUser
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from pas.plugins.proxy import pppMessageFactory as _
from pas.plugins.proxy.custom_fields import ProxyValueField
from pas.plugins.proxy.interfaces import IProxyRolesSettings
from plone import api
from plone.app.registry.browser import controlpanel
from z3c.form import button
from z3c.form import interfaces
from z3c.form.form import applyChanges
from z3c.form.interfaces import WidgetActionExecutionError
from zope.i18nmessageid import MessageFactory
from zope.interface import Invalid

pmf = MessageFactory('plone')

class UnrestrictedMember(UnrestrictedUser):
    """Unrestricted user that still has an id."""
    def getId(self):
        """Return the ID of the user."""
        return self.getUserName()


class ProxyRolesSettingsEditForm(controlpanel.RegistryEditForm):
    """ Proxy roles settings form """
    schema = IProxyRolesSettings
    id = "ProxyRolesSettingsEditForm"
    label = _(u"Proxy Roles Settings")
    description = _(u"help_proxyroles_settings_editform",
                    default=u"Set proxy roles.")

    def updateWidgets(self):
        super(ProxyRolesSettingsEditForm, self).updateWidgets()
        user = api.user.get_current()
        portal = api.portal.get()
        #self.widgets['version_number'].mode = interfaces.HIDDEN_MODE
        if not user.checkPermission('pas.plugins.proxy: Manage proxy roles',
                                portal):
            # if user can't manage proxies, set delegators widgets to readonly mode
            for roles_widget in self.widgets['proxy_roles'].widgets:
                roles_widget.subform.widgets['delegator'].mode = interfaces.DISPLAY_MODE

    def validate_values(self, data):
        """
        If there are duplicate entries, return an error.
        If an username doesn't exist, return an error.
        If the current user tries to delegate different users, and doesn't have
        the right permission, return an error.
        If the current user A tries to delegate a user B that already delegate A, return an error
        BBB TO BE DONE - avoid circular delegation
        """
        proxy_roles = [(getattr(x, 'delegator', ''),
                        getattr(x, 'delegated', '')) for x in data.get('proxy_roles', [])]
        if len(proxy_roles) != len(set(proxy_roles)):
            return _(u"Do not duplicate entries.")
        for delegator, delegated in proxy_roles:
            if not api.user.get(username=delegated) or not api.user.get(username=delegator):
                return _(u"You should select an existent username.")
            user = api.user.get_current()
            if not user.checkPermission(
                'pas.plugins.proxy: Manage proxy roles',
                self.context) and user.getProperty('id') != delegator:
                return _(u"You cannot delegate other users.")
            # avoid cross delegation
            for subdelegator, subdelegated in proxy_roles:
                if delegator==subdelegated and delegated==subdelegator:
                    return _('cross_delegation_error',
                             default=u"${subdelegator} cannot delegate ${delegated}.\n"
                                     u"You cannot cross-delegate:\n"
                                     u"a user can't be delegator and delegated of another",
                             mapping={'subdelegator': subdelegator, 'delegated': subdelegated})
        return None

    @button.buttonAndHandler(pmf('Save'), name='save')
    def handleSave(self, action):
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
        #we need to set new security manager, to update catalog correctly
        catalog = api.portal.get_tool(name='portal_catalog')
        acl_users = api.portal.get_tool('acl_users')
        try:
            old_sm = getSecurityManager()
            tmp_user = UnrestrictedMember(old_sm.getUser().getId(), '', ['Manager'], '')
            tmp_user = tmp_user.__of__(acl_users)
            newSecurityManager(None, tmp_user)
            catalog.reindexIndex('allowedRolesAndUsers', self.request)
        finally:
            setSecurityManager(old_sm)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"),
                                                      "info")
        self.context.REQUEST.RESPONSE.redirect("@@proxy-roles-settings")

    @button.buttonAndHandler(pmf('Cancel'), name='cancel')
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
    """Settings control panel"""
    index = ViewPageTemplateFile('controlpanel.pt')
    form = ProxyRolesSettingsEditForm
