#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright 2015 Fabian Grimme

This file is part of DiscoPy.

DiscoPy is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any late
version.
DiscoPy is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
DiscoPy. If not, see <http://www.gnu.org/licenses/>.
"""

import requests


class ImageHandler(object):

    def get_file(self, filepath, url, headers=None, params=None):
        response = requests.get(url, headers=headers, params=params, stream=True)

        if response.status_code == 200 or response.status_code == 301 or response.status_code == 307:
            with open(unicode(filepath), 'wb') as file_:
                for chunk in response.iter_content():
                    file_.write(chunk)
        else:
            raise Exception('unable to fetch image: %s %s' % (url, response.status_code))
