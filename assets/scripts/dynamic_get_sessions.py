from functools import cached_property
from zeep import Client, helpers
from typing import Any

WSDL_URL = "http://webservices.legis.ga.gov/Legislation/Service.svc?wsdl"

class GALegisSessionHelper:
    def __init__(self, wsdl: str = WSDL_URL):
        self.client = Client(wsdl)

    # ---------- helpers ---------- #
def _get_sessions_op(self):
    for candidate in ("GetSessions", "GetLegislativeSessions"):
        if candidate in self.client.service._binding._operations:
            return getattr(self.client.service, candidate)
    raise RuntimeError("Sessions operation not found in WSDL!")

@cached_property
def sessions(self):
    """Return a list of session dicts, or [] if the WSDL has no session op."""
    try:
        resp = self._get_sessions_op()()
    except RuntimeError:
        return []                      # Legislation WSDL doesn’t expose sessions
    return helpers.serialize_object(resp, target_cls=dict)  # type: ignore[arg-type]

# -------------- use it -------------- #
if __name__ == "__main__":
    helper = GALegisSessionHelper()
    if helper.sessions:
        for s in helper.sessions:
            print(f"{s['Id']}: {s['Description']}")
    else:
        print("This WSDL has no session list.")