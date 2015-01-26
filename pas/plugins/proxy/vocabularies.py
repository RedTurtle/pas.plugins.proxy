# -*- coding: utf-8 -*-
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from plone import api


class UsersVocabulary(object):
    """
    Vocabulary factory for available users.
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        available_users = api.user.get_users()
        users = []
        for user in available_users:
            userid = user.getProperty('id')
            fullname = user.getProperty('fullname') or userid
            users.append(SimpleTerm(userid, userid, fullname))
        return SimpleVocabulary(users)

UsersVocabularyFactory = UsersVocabulary()
