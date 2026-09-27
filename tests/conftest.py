"""
conftest for v6 swarm tests.
Sets ASAS_NO_RAY before modules are imported so SwarmWorker stays a plain class.
"""
import os
import sys

# Must set before any import of swarm modules
os.environ["ASAS_NO_RAY"] = "1"

# Force re-import of swarm modules without Ray decoration
mods_to_reload = [k for k in sys.modules if "asas_agent.distributed" in k]
for m in mods_to_reload:
    del sys.modules[m]
