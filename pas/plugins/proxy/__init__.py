# -*- coding: utf-8 -*-

import logging
from zope.i18nmessageid import MessageFactory
from AccessControl.Permissions import add_user_folders

logger = logging.getLogger('pas.plugins.proxy')
pppMessageFactory = MessageFactory('pas.plugins.proxy')

from pas.plugins.proxy.plugin import ProxyUserRolesManager, AddForm

def initialize(context):
    """Initializer called when used as a Zope 2 product."""

    context.registerClass(ProxyUserRolesManager,
        permission=add_user_folders,
        constructors=(AddForm,),
        visibility=None,
        icon='browser/static/proxy.png'
        )
