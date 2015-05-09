# -*- coding: utf-8 -*-

import unittest

from pas.plugins.proxy.interfaces import IPasPluginsProxyLayer
from pas.plugins.proxy.interfaces import IProxyRolesSettings
from plone.registry.interfaces import IRegistry
from zope import interface
from zope.component import queryUtility
from zope.annotation.interfaces import IAnnotations


class BaseTestCase(unittest.TestCase):

    def getSettings(self):
        registry = queryUtility(IRegistry)
        return registry.forInterface(IProxyRolesSettings, check=False)

    def markRequestWithLayer(self):
        # to be removed when p.a.testing will fix https://dev.plone.org/ticket/11673
        request = self.layer['request']
        interface.alsoProvides(request, IPasPluginsProxyLayer)

    def clean_request(self):
        req_annotations = IAnnotations(self.layer['request'])
        for key in ('ppp.getGroupsForPrincipal', 'ppp.getRolesForPrincipal',
                    'ppp.getRolesInContext', 'ppp.user', 'ppp.checkLocalRolesAllowed'):
            if key in req_annotations.keys():
                del req_annotations[key]
