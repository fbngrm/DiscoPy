#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright 2015 Fabian Grimme

This file is part of DiscoPy.

DiscoPy is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
DiscoPy is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with D
"""

import re


class NameBuilder(object):

    def build_name(self, syntax, release_data, track_data):
        """Build a filename by substituting syntax keywords by it's equivalents from the provided data. Ensure the filename does not contain directory seperator characters.
        """

        options = {
            'artist': release_data['artist'].lower(),
            'Artist': self._capitalize(release_data['artist']),
            'ARTIST': release_data['artist'].upper(),
            'release': release_data['title'].lower(),
            'Release': self._capitalize(release_data['title']),
            'RELEASE': release_data['title'].upper(),
            'country': release_data['country'].lower(),
            'Country': self._capitalize(release_data['country']),
            'COUNTRY': release_data['country'].upper(),
            'genres': release_data['genres'].lower(),
            'Genres': self._capitalize(release_data['genres']),
            'GENRES': release_data['genres'].upper(),
            'label': release_data['label'].lower(),
            'Label': self._capitalize(release_data['label']),
            'LABEL': release_data['label'].upper(),
            'year': release_data['year'],
            'Year': release_data['year'],
            'YEAR': release_data['year'],
            'index': track_data['index'].zfill(2).lower() if track_data else '',
            'Index': track_data['index'].zfill(2).upper()if track_data else '',
            'INDEX': track_data['index'].zfill(2).upper()if track_data else '',
            'track': track_data['title'].lower() if track_data else '',
            'Track': self._capitalize(track_data['title']) if track_data else '',
            'TRACK': track_data['title'].upper() if track_data else ''
        }

        for option in options.keys():
            if option in syntax:
                syntax = syntax.replace(option, options[option]).strip()

        return re.sub('[\\\/]+', '-', syntax)

    def _capitalize(self, s):
        res = ''
        for word in s.split(' '):
            try:
                res = '%s %s' % (res, word[0].capitalize())
                if len(word) > 1:
                    res = '%s%s' % (res, word[1:])
            except:
                res = '%s %s' % (res, word)
        return res.strip()
