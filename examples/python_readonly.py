"""Run after pip installing the local wheel. No network access needed."""
import json
from rootstock_tools import Toolchain
sdk=Toolchain()
for operation in ('registry.list_networks','capabilities.list','skills.list'):
    print(json.dumps({'capability':operation,'data':sdk.run(operation)},indent=2))
