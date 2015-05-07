# -*- coding: utf-8 -*-

from zope.configuration import xmlconfig
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID


class ProxyRolesLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        # Load ZCML for this package
        import pas.plugins.proxy
        xmlconfig.file('configure.zcml',
                       pas.plugins.proxy,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'pas.plugins.proxy:default')
        applyProfile(portal, 'pas.plugins.proxy:test')
        setRoles(portal, TEST_USER_ID, ['Member', 'Manager'])
        acl_users = portal.acl_users
        acl_users.userFolderAddUser('user1', 'secret', ['Member', ], [])
        acl_users.userFolderAddUser('user2', 'secret', ['Member', ], [])
        acl_users.userFolderAddUser('user3', 'secret', ['Member', ], [])


PROXYROLES_FIXTURE = ProxyRolesLayer()
PROXYROLES_INTEGRATION_TESTING = \
    IntegrationTesting(bases=(PROXYROLES_FIXTURE, ),
                       name="ProxyRoles:Integration")
PROXYROLES_FUNCTIONAL_TESTING = \
    FunctionalTesting(bases=(PROXYROLES_FIXTURE, ),
                      name="ProxyRoles:Functional")

