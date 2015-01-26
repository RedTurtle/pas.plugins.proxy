# -*- coding: utf-8 -*-
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from pas.plugins.proxy.plugin import ProxyUserRolesManager
from pas.plugins.proxy import logger
from pas.plugins.proxy import config


def installPASPlugin(portal, name, klass, title):

    userFolder = portal['acl_users']
    if name not in userFolder:
        plugin = klass(name, title)
        userFolder[name] = plugin
        # Activate all interfaces
        activatePluginInterfaces(portal, name)
        # Move plugin to the top of the list for each active interface
        plugins = userFolder['plugins']
        for info in plugins.listPluginTypeInfo():
            interface = info['interface']
            if plugin.testImplements(interface):
                active = list(plugins.listPluginIds(interface))
                if name in active:
                    active.remove(name)
                    active.insert(0, name)
                    plugins._plugins[interface] = tuple(active)
        logger.info('%s plugin created' % title)


def importVarious(context):
    """Miscellanous steps import handle
    """
    if context.readDataFile('pas.plugins.proxy-various.txt') is None:
        return

    portal = context.getSite()
    installPASPlugin(portal,
                     config.PLUGIN_ID,
                     ProxyUserRolesManager,
                     'Proxy User Roles Plugin')
