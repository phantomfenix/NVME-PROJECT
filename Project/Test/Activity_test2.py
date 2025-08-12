#!/bin/env python3.9
import subprocess
import json
## @class Activitytest2
class Activitytest2:
    def __init__(self, nvme_interface=None, Logger=None):
        self.nvme_interface = nvme_interface
        self.logger = logger or print 