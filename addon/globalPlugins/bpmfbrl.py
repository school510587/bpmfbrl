# -*- coding: UTF-8 -*-
# Copyright (C) 2025 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from addonHandler import AddonError
from nvwave import playErrorSound
import globalPluginHandler
import louis

EXPECTED_LIBLOUIS_MERGE = "3.35.0"
split_version = lambda v: tuple(map(int, v.split(".")))
if split_version(louis.version()) >= split_version(EXPECTED_LIBLOUIS_MERGE):
    playErrorSound()
    raise AddonError("The liblouis version {0} is not less than {1}".format(louis.version(), EXPECTED_LIBLOUIS_MERGE))

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    pass
