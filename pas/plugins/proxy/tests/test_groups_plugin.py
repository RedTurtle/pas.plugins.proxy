# -*- coding: utf-8 -*-

from pas.plugins.proxy.testing import PROXYROLES_INTEGRATION_TESTING
from pas.plugins.proxy.custom_fields import ProxyValueField
from pas.plugins.proxy.tests.base import BaseTestCase
from plone import api
from plone.app.testing import login
from plone.app.testing import logout


class PASPluginGroupsLocalRolesTestCase(BaseTestCase):
    
    layer = PROXYROLES_INTEGRATION_TESTING

    def setUp(self):
        self.markRequestWithLayer()
        portal = self.layer['portal']
        settings = self.getSettings()
        settings.proxy_roles = (ProxyValueField('user1', 'user2'), 
                                ProxyValueField('user2', 'user3'),)
        portal.invokeFactory('Folder', 'folder', title='Folder A')
        self.folder = portal.folder
        self.folder.invokeFactory('Folder', 'subfolder', title='Folder B')
        api.group.create(groupname='staff')
        api.group.add_user(groupname='staff', username='user1')
        self.folder.manage_addLocalRoles('staff', ('Editor', ))
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

    def test_normal_user_roles_acquired(self):
        """Tests that a delegator roles is not influenced by proxy his roles"""
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder/subfolder')
        login(portal, 'user1')
        output = self.folder.subfolder()
        self.assertTrue(u'id="contentview-edit"' in output) # can edit
        self.assertTrue('Editor' in api.user.get_roles(username='user1', obj=self.folder.subfolder))

    def test_delegated_get_roles(self):
        """Tests that a delegated user take delegator's roles"""
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder')
        login(portal, 'user2')
        output = self.folder()
        self.assertTrue(u'id="contentview-edit"' in output) # can edit
        self.assertTrue('Editor' in api.user.get_roles(username='user2', obj=self.folder))

    def test_delegated_get_roles_acquired(self):
        """Tests that a delegated user take delegator's roles"""
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder/subfolder')
        login(portal, 'user2')
        output = self.folder.subfolder()
        self.assertTrue(u'id="contentview-edit"' in output) # can edit
        self.assertTrue('Editor' in api.user.get_roles(username='user2', obj=self.folder.subfolder))


class PASPluginGroupsGlobalRolesTestCase(BaseTestCase):
    
    layer = PROXYROLES_INTEGRATION_TESTING

    def setUp(self):
        self.markRequestWithLayer()
        portal = self.layer['portal']
        settings = self.getSettings()
        settings.proxy_roles = (ProxyValueField('user1', 'user2'), 
                                ProxyValueField('user2', 'user3'),)
        portal.invokeFactory('Folder', 'folder', title='Folder A')
        self.folder = portal.folder
        api.group.create(groupname='staff')
        api.group.add_user(groupname='staff', username='user1')
        api.group.grant_roles(groupname='staff', roles=['Editor'])
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
