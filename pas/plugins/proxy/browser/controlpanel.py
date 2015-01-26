# -*- coding: utf-8 -*-
from plone.app.registry.browser import controlpanel
from Products.statusmessages.interfaces import IStatusMessage
from pas.plugins.proxy import pppMessageFactory as _
from pas.plugins.proxy.interfaces import IProxyRolesSettings
from z3c.form import button
from plone import api


class ProxyRolesSettingsEditForm(controlpanel.RegistryEditForm):
    """Media settings form.
    """
    schema = IProxyRolesSettings
    id = "ProxyRolesSettingsEditForm"
    label = _(u"Proxy Roles Settings")
    description = _(u"help_proxyroles_settings_editform",
                    default=u"Set proxy roles.")

    @button.buttonAndHandler(_('Save'), name='save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        changes = self.applyChanges(data)
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


class ProxyRolesControlPanel(controlpanel.ControlPanelFormWrapper):
    """Sitesearch settings control panel.
    """
    form = ProxyRolesSettingsEditForm
