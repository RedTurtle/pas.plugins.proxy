# -*- coding: utf-8 -*-

import unittest

from Products.CMFCore.utils import getToolByName
from pas.plugins.proxy.interfaces import IPasPluginsProxyLayer
from pas.plugins.proxy.interfaces import IProxyRolesSettings
from pas.plugins.proxy.testing import PROXYROLES_INTEGRATION_TESTING
from pas.plugins.proxy.custom_fields import ProxyValueField
from pas.plugins.proxy.tests.base import BaseTestCase
from plone import api
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.registry.interfaces import IRegistry
from zope import interface
from zope.component import queryUtility
from zope.annotation.interfaces import IAnnotations



class PASPluginGlobalRolesTestCase(BaseTestCase):
    
    layer = PROXYROLES_INTEGRATION_TESTING

    def setUp(self):
        self.markRequestWithLayer()
        portal = self.layer['portal']
        settings = self.getSettings()
        settings.proxy_roles = (ProxyValueField('user1', 'user2'), 
                                ProxyValueField('user2', 'user3'),)
        portal.invokeFactory('Folder', 'folder', title='Folder A')
        self.folder = portal.folder
        setRoles(portal, 'user1', ['Editor'])
        setRoles(portal, 'user2', ['Contributor'])
        self.clean_request()

    def tearDown(self):
        logout()

    def test_normal_user_roles(self):
        """Tests that a delegator roles is not influenced by proxy his roles"""
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder')
        login(portal, 'user1')
        output = self.folder()
        self.assertTrue(u'id="contentview-edit"' in output) # can edit
        self.assertTrue('Editor' in api.user.get_roles(username='user1', obj=self.folder))

    def test_delegated_get_roles(self):
        """Tests that a delegated user take delegator's roles"""
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder')
        login(portal, 'user2')
        output = self.folder()
        self.assertTrue(u'id="contentview-edit"' in output) # can edit
        self.assertTrue('Editor' in api.user.get_roles(username='user2', obj=self.folder))
        self.assertTrue('Delegate' in api.user.get_roles(username='user2', obj=self.folder))

    def test_2nd_lev_delegated(self):
        """Tests that:
           a delegated user (3) from a delegator (2) already delegate from a master delegator (1)
           get roles from direct delegator (2) but not from master delegator in chain (1)
        """
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder')
        login(portal, 'user3')
        output = self.folder()
        self.assertTrue(u'Add new\u2026' in output) # can add
        self.assertFalse(u'id="contentview-edit"' in output) # can't edit
        roles = api.user.get_roles(username='user3', obj=self.folder)
        self.assertTrue('Contributor' in roles)
        self.assertFalse('Editor' in roles)

