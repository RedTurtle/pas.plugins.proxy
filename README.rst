A **PAS plugin** for Plone where administrators (or normal users) can
**delegate their own permissions** to other users.

.. contents:: **Table fo contents**

Introduction
============

This product will add a role sharing control panel to you site, where a user
(the **delegator**) will be able to *proxy* his roles to another user
(**delegate**).

While the delegation is active, the delegate will be able to act as the
delegator, as he own *same roles* (both global and local).

Every delegate will also gain a new *Delegate* role (this role will not be
registered in your Plone site, this feature must be activated by 3rd party
configuration).

The "*Proxy Roles Settings*" control panel
==========================================

The plugin configuration is composed by a sequence of delegator/delegate
couples.

.. image:: https://github.com/RedTurtle/pas.plugins.proxy/blob/8e78343869d00154b45395d007c66c841357e285/docs/pas.plugins.proxy-0.1.0-01.png
   :alt: Proxy Roles Settings

By default *all* users can access this panel, with a big difference:

* Managers and Site Administrators (who own
  "``pas.plugins.proxy: Manage proxy roles``" permission) can add and delete
  roles delegations for all users
* Other members can only delegate for themself. If you don't want to give this
  power to normal users you can just remove the
  "``pas.plugins.proxy: Access proxy roles panel``" permission.

Other rules:

* You can only delegate for existings usernames
* Cannot cross-delegate (a user can't be both delegator and delegate of
  another)
* A delegator can proxy his roles as many times as he need
* A user can be delegate of many users 

Groups
======

The PAS plugin act also as a group plugin: the delegate will automatically gets
all roles (again: global and local) given to groups where the delegator is in. 

Ask for groups of delegate will get you groups of his delegator.
Instead: asking for users of a group will not return users that seems part of
the groups thanks to delegation process.

Limitations and Troubleshooting
===============================

The most important thing to know: the **plugin works only for currently logged
in user** (someway similar to the Authenticated Users virtual group): if you
query the permissions of a delegate by code you will get nothing.
This is not a technical limit but a practical consequence of aggressive cache
done by the plugin itself, bringing us acceptable performance.

Delegation works with **one-level of inheritance**: in user A is delegator of
user B, and user B is delegator of user C, C will not get any power from A.
This could probably possibile in future (if so: optionally) but there are some
implications about performance and avoiding circular delegations loops.

There's no simple way to know if a user is able to perform an action because he
has sufficient permissions or because he get the needed permission thanks to
a delegator's role.
Neither the *Delegate* role can help too much for this, as it's given every
time a role's proxy is active on the current context.

Authors
=======

This product was developed by RedTurtle Technology team.

.. image:: http://www.redturtle.it/redturtle_banner.png
   :alt: RedTurtle Technology Site
   :target: http://www.redturtle.it/
