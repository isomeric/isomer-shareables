#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer Application Framework
# ============================
# Copyright (C) 2011-2019 Heiko 'riot' Weinen <riot@c-base.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

"""


Module: Shareables
==================


"""

from isomer.component import ConfigurableComponent, handler
from isomer.database import objectmodels
from isomer.logger import debug, error
from isomer.events.system import authorized_event
from isomer.events.client import send


# from pprint import pprint


class reserve(authorized_event):
    """Reserves a shareable object"""


class Manager(ConfigurableComponent):
    """
    Manages shareable resources.
    """
    channel = 'isomer-web'

    configprops = {
    }

    def __init__(self, *args):
        """
        Initialize the ShareableWatcher component.

        :param args:
        """

        super(Manager, self).__init__("SHAREABLE", *args)

        self.log("Started")

    def objectcreation(self, event):
        if event.schema == 'shareable':
            self.log("Updating shareables")

    @handler(reserve)
    def reserve(self, event):
        try:
            uuid = event.data['uuid']
            reserve_from = event.data['from']
            reserve_to = event.data['to']
            reserve_title = None if 'title' not in event.data else \
                event.data['title']
            reserve_description = "" if 'description' not in event.data \
                else event.data['description']

            shareable_model = objectmodels['shareable']
            shareable = shareable_model.find_one({'uuid': uuid})

            early = shareable_model.find_one({
                'uuid': uuid,
                'reservations': {
                    '$elemMatch': {
                        'starttime': {'$lte': reserve_from},
                        'endtime': {'$gte': reserve_from}
                    }
                }
            })

            self.log('Any early reservation:', early, lvl=debug)

            late = shareable_model.find_one({
                'uuid': uuid,
                'reservations': {
                    '$elemMatch': {
                        'starttime': {'$lte': reserve_to},
                        'endtime': {'$gte': reserve_to}
                    }
                }
            })

            self.log('Any late reservation:', late, lvl=debug)

            if not late and not early:
                reservation = {
                    'useruuid': event.user.uuid,
                    'starttime': reserve_from,
                    'endtime': reserve_to,
                    'title': reserve_title if reserve_title else
                    "Reserved by " + event.user.account.name,
                    'description': reserve_description
                }
                shareable.reservations.append(reservation)
                shareable.save()
                self.log('Successfully stored reservation!')
                response = {
                    'component': 'isomer.shareables.manager',
                    'action': 'reserve',
                    'data': True
                }
            else:
                self.log('Not able to store reservation due to '
                         'overlapping reservations.')
                response = {
                    'component': 'isomer.shareables.manager',
                    'action': 'reserve',
                    'data': False
                }
            self.fireEvent(send(event.client.uuid, response))
        except Exception as e:
            self.log('Unknown failure:', e, type(e), exc=True)
