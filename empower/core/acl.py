#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

"""EmPOWER ACL."""


class ACL:
    """An user ACL."""

    def __init__(self, addr, label=""):

        self.__addr = addr
        self.__label = label

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        return {'addr': self.addr,
                'label': self.label}

    @property
    def addr(self):
        """Get addr."""

        return self.__addr

    @property
    def label(self):
        """Get label."""

        return self.__label

    def __str__(self):
        return str(self.addr)

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, ACL):
            return self.addr == other.addr
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
