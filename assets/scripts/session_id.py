# Returns the latest SessionID where at least one bill is present in the feed. 
#This is a quick way to determine which session ID is active. 

from zeep import Client
wsdl = "http://webservices.legis.ga.gov/Legislation/Service.svc?wsdl"
c = Client(wsdl)

def first_live_session(max_id: int = 35, min_id: int = 20):
    """Return the newest SessionId whose feed contains at least one bill."""
    for sid in range(max_id, min_id - 1, -1):          # 35 → 20
        resp = c.service.GetLegislationForSession(SessionId=sid)
        if resp is None:               # ← feed empty, keep looking
            continue
        if len(resp):                  # non-empty iterable
            return sid, len(resp)
    return None, 0                     # nothing found

sid, count = first_live_session()
if sid:
    print(f"SOAP feed reports {count} bills for SessionId {sid}")
else:
    print("No active session found in specified range.")