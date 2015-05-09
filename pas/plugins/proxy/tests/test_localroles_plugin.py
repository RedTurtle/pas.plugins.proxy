# -*- coding: utf-8 -*-

from pas.plugins.proxy.testing import PROXYROLES_INTEGRATION_TESTING
from pas.plugins.proxy.custom_fields import ProxyValueField
from pas.plugins.proxy.tests.base import BaseTestCase
from plone import api
from plone.app.testing import login
from plone.app.testing import logout


class PASPluginLocalRolesTestCase(BaseTestCase):
    
    layer = PROXYROLES_INTEGRATION_TESTING

    def setUp(self):
        self.markRequestWithLayer()
        portal = self.layer['portal']
        settings = self.getSettings()
        settings.proxy_roles = (ProxyValueField('user1', 'user2'), 
                                ProxyValueField('user2', 'user3'),
                                ProxyValueField('user4', 'user5'),
                                )
        portal.invokeFactory('Folder', 'folder', title='Folder A')
        self.folder = portal.folder
        self.folder.invokeFactory('Folder', 'subfolder', title='Folder B')
        self.folder.manage_addLocalRoles('user1', ('Editor', ))
        self.folder.manage_addLocalRoles('user2', ('Contributor', ))
        self.folder.manage_addLocalRoles('user4', ('Reader', ))
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

    def test_delegated_get_access(self):
        """Tests that a delegated user take simple power like View"""
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder')
        login(portal, 'user5')
        output = self.folder()
        self.assertTrue(u'There are currently no items in this folder.' in output) # see the emtpy folder
        self.assertTrue('Reader' in api.user.get_roles(username='user5', obj=self.folder))

    def test_delegated_get_delegate_permission(self):
        # Tests that Delegate role works normally with workflow, permissions, ...
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder')
        login(portal, 'user3')
        user = api.user.get('user3')
        output = self.folder()
        self.assertTrue('plone-contentmenu-display' in output)
        self.assertTrue(user.checkPermission('Modify view template', self.folder))

    def test_delegated_get_roles_acquired(self):
        """Tests that a delegated user acquire delegator's roles from parents"""
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder/subfolder')
        request.set('URL', 'http://nohost/plone/folder/subfolder')
        login(portal, 'user2')
        output = self.folder.subfolder()
        self.assertTrue(u'id="contentview-edit"' in output) # can edit
        self.assertTrue('Editor' in api.user.get_roles(username='user2', obj=self.folder.subfolder))
        self.assertTrue('Delegate' in api.user.get_roles(username='user2', obj=self.folder.subfolder))

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
        self.assertTrue('Delegate' in roles)

    def test_2nd_lev_delegated_acquired(self):
        """Tests that:
           a delegated user (3) from a delegator (2) already delegate from a master delegator (1)
           get roles from direct delegator (2) but not from master delegator in chain (1)
        """
        portal = self.layer['portal']
        request = self.layer['request']
        request.set('ACTUAL_URL', 'http://nohost/plone/folder/subfolder')
        login(portal, 'user3')
        output = self.folder.subfolder()
        self.assertTrue(u'Add new\u2026' in output) # can add
        self.assertFalse(u'id="contentview-edit"' in output) # can't edit
        roles = api.user.get_roles(username='user3', obj=self.folder.subfolder)
        self.assertTrue('Contributor' in roles)
        self.assertFalse('Editor' in roles)
        self.assertTrue('Delegate' in roles)

    def test_delegation_work_only_for_current_user(self):
        # This test is showing one of the limitation of the plugin: delegation only work
        # for current logged in user (this in consequence of caching on request, but removing caghing
        # is perfomance killer 
        portal = self.layer['portal']
        login(portal, 'user2')
        roles = api.user.get_roles(username='user3', obj=self.folder.subfolder)
        self.assertFalse('Contributor' in roles)
        self.assertFalse('Delegate' in roles)

    