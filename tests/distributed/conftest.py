"""
conftest for distributed tests.
Sets ASAS_NO_RAY before modules are imported so SwarmWorker stays a plain class.
"""
import os
import sys

os.environ["ASAS_NO_RAY"] = "1"
mods_to_reload = [k for k in sys.modules if "asas_agent.distributed" in k]
for m in mods_to_reload:
    del sys.modules[m]
