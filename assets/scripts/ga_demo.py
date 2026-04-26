from zeep import Client, helpers

session_client = Client("http://webservices.legis.ga.gov/Session/Service.svc?wsdl")
legis_client   = Client("http://webservices.legis.ga.gov/Legislation/Service.svc?wsdl")

# --- 1) Fetch session catalogue ---------------------------------
sessions_raw = session_client.service.GetLegislativeSessions()
sessions = helpers.serialize_object(sessions_raw, target_cls=dict)
for s in sessions:
    print(f"SessionId {s['Id']}  →  {s['Description']}")

# Decide which Id you want; if you need the newest with data, run the probe:
def first_live_session(cid_max=40, cid_min=20):
    for sid in range(cid_max, cid_min - 1, -1):
        resp = legis_client.service.GetLegislationForSession(SessionId=sid)
        if resp is not None and len(resp):
            return sid
    return None

LIVE_SESSION_ID = first_live_session()
print("\nFirst session that actually has bills in the Legislation feed:", LIVE_SESSION_ID)

# --- 2) Run a simple search in that session ----------------------
if LIVE_SESSION_ID:
    result = legis_client.service.GetLegislationSearchResultsPaged(
        Constraints={"Session": {"Id": LIVE_SESSION_ID}},
        PageSize=5,
        StartIndex=0,
    )
    page = helpers.serialize_object(result, target_cls=dict)["Page"]["LegislationSearchResult"]
    print("\nSample bills:")
    for bill in page:
        print(f"• {bill['DocumentType']} {bill['Number']}  {bill['Caption']}")
else:
    print("No populated sessions found in the current range.")