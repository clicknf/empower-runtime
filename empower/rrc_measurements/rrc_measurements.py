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

"""RRC measurements module."""

from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import Array
from construct import BitStruct
from construct import Padding
from construct import Bit

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.core.module import ModuleTrigger
from empower.vbsp import PT_VERSION
from empower.vbsp import E_TYPE_TRIG
from empower.vbsp import EP_DIR_REQUEST
from empower.vbsp import EP_OPERATION_ADD

from empower.main import RUNTIME


EP_ACT_RRC_MEASUREMENT = 0x05

RRC_REQUEST = Struct("rrc_request",
                     UBInt32("length"),
                     UBInt8("type"),
                     UBInt8("version"),
                     UBInt32("enbid"),
                     UBInt16("cellid"),
                     UBInt32("modid"),
                     UBInt32("seq"),
                     UBInt8("action"),
                     UBInt8("dir"),
                     UBInt8("op"),
                     UBInt8("meas_id"),
                     UBInt16("rnti"),
                     UBInt16("earfcn"),
                     UBInt16("interval"),
                     UBInt16("max_cells"),
                     UBInt16("max_meas"))

RRC_ENTRY = Sequence("rrc_entries",
                     UBInt8("meas_id"),
                     UBInt16("pci"),
                     UBInt16("rsrp"),
                     UBInt16("rsrq"))

RRC_RESPONSE = Struct("rrc_response",
                      UBInt32("nof_meas"),
                      Array(lambda ctx: ctx.nof_meas, RRC_ENTRY))


class RRCMeasurements(ModuleTrigger):
    """ LVAPStats object. """

    MODULE_NAME = "rrc_measurements"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'imsi', 'measurements']

    def __init__(self):

        super().__init__()

        # parameters
        self._imsi = None
        self._measurements = []

        # stats
        self.results = []

        # set this for auto-cleanup
        self.vbs = None

    def __eq__(self, other):

        return super().__eq__(other) and self.imsi == other.imsi and \
            self.measurements == other.measurements

    @property
    def measurements(self):
        """Return measurements."""

        return self._measurements

    @measurements.setter
    def measurements(self, value):
        """Set measurements."""

        for meas in value:

            measurement = {
                "earfcn": int(meas["earfcn"]),
                "interval": int(meas["interval"]),
                "max_cells": int(meas["max_cells"]),
                "max_meas": int(meas["max_meas"])
            }

            self._measurements.append(measurement)

    @property
    def imsi(self):
        """Return the imsi."""

        return self._imsi

    @imsi.setter
    def imsi(self, value):
        """Set IMSI Address."""

        self._imsi = int(value)

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['imsi'] = self.imsi
        out['measurements'] = self.measurements
        out['results'] = self.results

        return out

    def run_once(self):
        """Send out rate request."""

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.imsi not in tenant.ues:
            self.log.info("UE %u not found", self.imsi)
            self.unload()
            return

        ue = tenant.ues[self.imsi]

        if not ue.vbs or not ue.vbs.is_online():
            self.log.info("VBS %s not connected", ue.vbs.addr)
            self.unload()
            return

        self.vbs = ue.vbs

        for i in range(0, len(self.measurements)):

            measurement = self.measurements[i]

            rrc_request = Container(length=34,
                                    type=E_TYPE_TRIG,
                                    version=PT_VERSION,
                                    enbid=self.vbs.enb_id,
                                    cellid=ue.cell.pci,
                                    modid=self.module_id,
                                    seq=self.vbs.seq,
                                    action=EP_ACT_RRC_MEASUREMENT,
                                    dir=EP_DIR_REQUEST,
                                    op=EP_OPERATION_ADD,
                                    meas_id=i,
                                    rnti=ue.rnti,
                                    earfcn=measurement["earfcn"],
                                    interval=measurement["interval"],
                                    max_cells=measurement["max_cells"],
                                    max_meas=measurement["max_meas"])

            self.log.info("Sending rrc request to %s @ %s (id=%u, meas_id=%u)",
                          ue.rnti, self.vbs.enb_id, self.module_id, i)

            msg = RRC_REQUEST.build(rrc_request)
            self.vbs.connection.stream.write(msg)

    def handle_response(self, meas):
        """Handle an incoming RRC_MEASUREMENTS message.
        Args:
            meas, a RRC_MEASUREMENTS message
        Returns:
            None
        """

        print(meas)

        # call callback
        self.handle_callback(self)


class RRCMeasurementsWorker(ModuleVBSPWorker):
    """ Counter worker. """

    pass


def rrc_measurements(**kwargs):
    """Create a new module."""

    module = RRCMeasurementsWorker.__module__
    return RUNTIME.components[module].add_module(**kwargs)


def bound_rrc_measurements(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return rrc_measurements(**kwargs)

setattr(EmpowerApp, RRCMeasurements.MODULE_NAME, bound_rrc_measurements)


def launch():
    """ Initialize the module. """

    return RRCMeasurementsWorker(RRCMeasurements,
                                 EP_ACT_RRC_MEASUREMENT,
                                 RRC_RESPONSE)
