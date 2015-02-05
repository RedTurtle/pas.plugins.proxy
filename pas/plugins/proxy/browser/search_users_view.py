# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from zope.component import getMultiAdapter
import json
from itertools import chain


class SearchUsersView(BrowserView):
    """
    View that return a list of searched users
    in json format for the autocomplete
    """

    def __call__(self):
        self.request.response.setHeader("Content-type", "application/json")
        search_term = self.request.form.get('search_term')
        if not search_term:
            return json.dumps([])
        pas_search = getMultiAdapter((self.context, self.request),
                                      name='pas_search')
        users = self.merge_search_results(
            chain(*[pas_search.searchUsers(**{field: search_term})
                for field in ['name', 'fullname', 'email']]), 'userid')
        users = [{'label': x.get('description', x.get('id')), 'value': x.get('id')} for x in users]
        return json.dumps(users)

    def merge_search_results(self, results, key):
        """Merge member search results.

        Based on PlonePAS.browser.search.PASSearchView.merge.
        """
        output = {}
        for entry in results:
            id = entry[key]
            if id not in output:
                output[id] = entry.copy()
            else:
                buf = entry.copy()
                buf.update(output[id])
                output[id] = buf

        return output.values()
