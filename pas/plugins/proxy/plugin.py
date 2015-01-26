"""
A Local Roles Plugin Implementation that respects Black Listing markers.

ie. containers/objects which denote that they do not wish to acquire local
roles from their containment structure.

"""
from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner, aq_parent
from App.class_init import InitializeClass
from plone import api
from plone.memoize import ram
from Products.Five.browser import BrowserView
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.plugins.local_role import LocalRolesManager
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin
from time import time
from zope.interface import implements


def _proxied_username_cachekey(method, self, username):
    """
    method for ramcache that store time and username
    """
    timestamp = time() // (60 * 2 * 1)
    return "%s:%s" % (timestamp, username)


def _proxy_username_cachekey(method, self, username):
    """
    method for ramcache that store time and username
    """
    timestamp = time() // (60 * 2 * 1)
    return "%s:%s" % (timestamp, username)


class AddForm(BrowserView):
    """Add form the PAS plugin
    """
    def __call__(self):
        if 'form.button.Add' in self.request.form:
            name = self.request.form.get('id')
            title = self.request.form.get('title')
            plugin = ProxyUserRolesManager(name, title)
            self.context.context[name] = plugin
            self.request.response.redirect(self.context.absolute_url() +
            '/manage_workspace?manage_tabs_message=Plugin+added.')
            return
        return self.index()


class ProxyUserRolesManager(LocalRolesManager):
    """Class incorporating local role storage with
    PlonePAS-specific local role permission checking.
    """

    meta_type = "Proxy User Roles Manager"
    security = ClassSecurityInfo()

    implements(
        IGroupsPlugin,
        IRolesPlugin,
        ILocalRolesPlugin,
        )

    def __init__(self, id, title=''):
        self._setId(id)
        self.title = title

    @ram.cache(_proxied_username_cachekey)
    def get_delegator_list(self, username):
        """
        for a given username, return a list of usernames that delegate him
        """
        proxy_roles = api.portal.get_registry_record('pas.plugins.proxy.interfaces.IProxyRolesSettings.proxy_roles')
        return [x.delegator for x in proxy_roles if x.delegated == username]

    @ram.cache(_proxy_username_cachekey)
    def get_delegated_list(self, username):
        """
        for a given username, return a list of delegated users
        """
        proxy_roles = api.portal.get_registry_record('pas.plugins.proxy.interfaces.IProxyRolesSettings.proxy_roles')
        return [x.delegated for x in proxy_roles if x.delegator == username]

    # IGroupsPlugin implementation
    def getGroupsForPrincipal(self, principal, request=None):
        delegators = self.get_delegator_list(principal.getId())
        groups = set()
        for delegator in delegators:
            delegator_groups = [x.getId() for x in api.group.get_groups(username=delegator)]
            groups.update(delegator_groups)
        return tuple(groups)

    #IRolesPlugin implementation
    security.declarePrivate('getRolesForPrincipal')
    def getRolesForPrincipal(self, principal, request=None):
        """
        return a list of global roles of the delegator user
        """
        delegators = self.get_delegator_list(principal.getId())
        roles = set()
        for delegator in delegators:
            # delegated role need to be checked
            # roles = api.user.get_roles(username=src_user)
            # from zope.globalrequest import getRequest
            # request = getRequest()
            # annotations = IAnnotations(request)
            # if annotations.get('proxy_roles') == principal.getId():
            #     roles.append('Delegated')
            roles.update(api.user.get_roles(username=delegator))
        return tuple(roles)

    # ILocalRolesPlugin implementation
    security.declarePrivate("getRolesInContext")
    def getRolesInContext(self, user, object):
        """
        return a list of global roles of the delegator user
        """
        delegators = self.get_delegator_list(user.getId())
        roles = set()
        for delegator in delegators:
            # delegated role need to be checked
            # roles = api.user.get_roles(username=src_user, obj=object)
            # from zope.globalrequest import getRequest
            # request = getRequest()
            # annotations = IAnnotations(request)
            # if annotations.get('proxy_roles') == user.getId():
            #     roles.append('Delegated')
            roles.update(api.user.get_roles(username=delegator, obj=object))
        return tuple(roles)

    #security.declarePrivate( 'checkLocalRolesAllowed' )
    def checkLocalRolesAllowed(self, user, object, object_roles):
        """
        append to principal_ids, also the ids of the delegated user
        """
        inner_obj = aq_inner(object)
        user_id = user.getId()

        group_ids = user.getGroups()
        principal_ids = list(group_ids)
        principal_ids.insert(0, user_id)
        delegators = self.get_delegator_list(user.getId())
        for delegator in delegators:
            # delegated role need to be checked
            # from zope.globalrequest import getRequest
            # request = getRequest()
            # annotations = IAnnotations(request)
            # annotations['proxy_roles'] = user_id
            delegator_groups = [x.getId() for x in api.group.get_groups(username=delegator)]
            principal_ids.extend(delegator_groups)
            principal_ids.insert(0, delegator)
        while 1:

            local_roles = getattr(inner_obj, '__ac_local_roles__', None)

            if local_roles and callable(local_roles):
                local_roles = local_roles()

            if local_roles:
                dict = local_roles

                for principal_id in principal_ids:
                    local_roles = dict.get(principal_id, [])

                    # local_roles is empty most of the time, where as
                    # object_roles is usually not.
                    if not local_roles:
                        continue

                    for role in object_roles:
                        if role in local_roles:
                            if user._check_context(object):
                                return 1
                            return 0

            inner = aq_inner(inner_obj)
            parent = aq_parent(inner)

            if getattr(inner_obj, '__ac_local_roles_block__', None):
                break

            if parent is not None:
                inner_obj = parent
                continue

            new = getattr(inner_obj, 'im_self', None)

            if new is not None:
                inner_obj = aq_inner(new)
                continue

            break

        return None

    def getAllLocalRolesInContext(self, context):
        """
        return a map of local roles.
        If a user has a local role, and he delegated his roles to other users,
        add these users to the role mapping
        """
        roles = {}
        object = aq_inner(context)
        while True:

            local_roles = getattr(object, '__ac_local_roles__', None)

            if local_roles and callable(local_roles):
                local_roles = local_roles()

            if local_roles:

                dict = local_roles

                for principal, localroles in dict.items():

                    if not principal in roles:
                        roles[principal] = set()

                    roles[principal].update(localroles)

                    #set also the proxied users
                    delegated_users = self.get_delegated_list(principal)
                    for userid in delegated_users:
                        if not userid in roles:
                            roles[userid] = set()
                        roles[userid].update(localroles)
            inner = aq_inner(object)
            parent = aq_parent(inner)

            if getattr(object, '__ac_local_roles_block__', None):
                break

            if parent is not None:
                object = parent
                continue

            new = getattr(object, 'im_self', None)

            if new is not None:
                object = aq_inner(new)
                continue

            break
        return roles

InitializeClass(ProxyUserRolesManager)
