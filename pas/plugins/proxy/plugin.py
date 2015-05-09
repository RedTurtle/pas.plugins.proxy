"""
A Local Roles Plugin Implementation that respects Black Listing markers.

ie. containers/objects which denote that they do not wish to acquire local
roles from their containment structure.

"""
from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner, aq_parent
from App.class_init import InitializeClass
from plone import api
from Products.Five.browser import BrowserView
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.plugins.local_role import LocalRolesManager
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin
from zope.interface import implements
from zope.annotation.interfaces import IAnnotations


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

    meta_type = "Proxy User's Roles Manager"
    security = ClassSecurityInfo()

    implements(
        IGroupsPlugin,
        IRolesPlugin,
        ILocalRolesPlugin,
        )

    def __init__(self, id, title=''):
        self._setId(id)
        self.title = title

    def get_delegators_of(self, username):
        """
        for a given username, return a list of usernames that delegate him
        """
        proxy_roles = api.portal.get_registry_record('pas.plugins.proxy.interfaces.IProxyRolesSettings.proxy_roles')
        return [x.delegator for x in proxy_roles if x.delegated == username]

    def get_my_delegateds(self, username):
        """
        for a given username, return a list of users delegated by him
        """
        proxy_roles = api.portal.get_registry_record('pas.plugins.proxy.interfaces.IProxyRolesSettings.proxy_roles')
        return [x.delegated for x in proxy_roles if x.delegator == username]

    # IGroupsPlugin implementation
    def getGroupsForPrincipal(self, principal, request=None):
        if principal.getId()=='AuthenticatedUsers':
            return tuple()

        request = request or self.REQUEST
        annotations = IAnnotations(request)
        if annotations.get('ppp.user', None)==None:
            annotations['ppp.user'] = principal.getId()
        elif annotations.get('ppp.user', None)!=principal.getId():
            return tuple()
        stored = annotations.get('ppp.getGroupsForPrincipal', None)
        if stored is not None:
            return stored

        delegators = self.get_delegators_of(principal.getId())
        groups = set()
        for delegator in delegators:
            original_delegator_groups = api.group.get_groups(username=delegator)
            #delegator_groups = [g.getId() for g in original_delegator_groups]
            # BBB: this prevent infinite proxy of groups of user A that proxy user B that proxy user C
            delegator_groups = [g.getId() for g in original_delegator_groups if delegator in g.getGroupMemberIds()]
            groups.update(delegator_groups)
        groups = tuple(groups)
        annotations['ppp.getGroupsForPrincipal'] = groups
        return groups

    #IRolesPlugin implementation
    security.declarePrivate('getRolesForPrincipal')
    def getRolesForPrincipal(self, principal, request=None):
        """
        Return a list of global roles of the delegator user
        """
        if principal.getId()=='AuthenticatedUsers':
            return tuple()

        request = request or self.REQUEST
        annotations = IAnnotations(request)
        if annotations.get('ppp.user', None)==None:
            annotations['ppp.user'] = principal.getId()
        elif annotations.get('ppp.user', None)!=principal.getId():
            return tuple()
        stored = annotations.get('ppp.getRolesForPrincipal', None)
        if stored is not None:
            return stored

        delegators = self.get_delegators_of(principal.getId())
        roles = set()
        for delegator in delegators:
            roles.update(api.user.get_roles(username=delegator) + ['Delegate'])
        roles = tuple(roles)
        annotations['ppp.getRolesForPrincipal'] = roles
        ### obj.get_local_roles
        return roles

    # ILocalRolesPlugin implementation
    security.declarePrivate("getRolesInContext")
    def getRolesInContext(self, user, object):
        """        
        Return a list of roles of the delegator user, plus the 'Delegate' role
        """
        request = self.REQUEST
        #inner_obj = aq_inner(object)
        annotations = IAnnotations(request)

        if annotations.get('ppp.user', None)==None:
            annotations['ppp.user'] = user.getId()
        elif annotations.get('ppp.user', None)!=user.getId():
            return tuple()
        stored = annotations.get('ppp.getRolesInContext', None)

        if stored is not None:
            return stored

        delegators = self.get_delegators_of(user.getId())
        roles = set()
        for delegator in delegators:
            roles.update(api.user.get_roles(username=delegator, obj=object) + ['Delegate'])
            #roles.update([[r for r in lr[1]] for lr in inner_obj.get_local_roles() if lr[0]==delegator])
        roles = tuple(roles)
        annotations['ppp.getRolesInContext'] = roles
        ### obj.get_local_roles
        return roles

    #security.declarePrivate( 'checkLocalRolesAllowed' )
    def checkLocalRolesAllowed(self, user, object, object_roles):
        """
        Check whether the user has access to object based
        on local roles. access is determined by a user's local roles
        including one of the object roles.
        
        return values: 0, 1, None
        - 1 success
        - 0 object context violation
        - None - failure
        """

        user_id = user.getId()
        request = self.REQUEST
        object_roles = list(tuple(object_roles)) # BBB: sometimes we get a tuple and duplicates

        annotations = IAnnotations(request)
        if annotations.get('ppp.user', None)==None:
            annotations['ppp.user'] = user_id
        elif annotations.get('ppp.user', None)!=user_id:
            return None

        inner_obj = aq_inner(object)

        principal_ids = annotations.get('ppp.checkLocalRolesAllowed', [])
        if not principal_ids:
            delegators = self.get_delegators_of(user_id)
            for delegator in delegators:
                delegator_groups = [x.getId() for x in api.group.get_groups(username=delegator)]
                principal_ids.extend(delegator_groups)
                principal_ids.insert(0, delegator)
    
            principal_ids = list(set(principal_ids))
            annotations['ppp.checkLocalRolesAllowed'] = principal_ids

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
        Return active all local roles in a context.

        The roles are returned in a dictionary mapping a principal (a
        user or a group) to the set of roles assigned to it.

        If a user has a local role, and he delegates his roles to other users,
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

#                    if not principal in roles:
#                        roles[principal] = set()
#
#                    roles[principal].update(localroles)

                    # set also the proxied users
                    delegated_users = self.get_my_delegateds(principal)
                    for userid in delegated_users:
                        if not userid in roles:
                            roles[userid] = set()
                        roles[userid].update(localroles + ['Delegate'])

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
