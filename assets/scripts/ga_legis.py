"""
ga_legis.py – Simple wrapper around the Georgia General Assembly SOAP service.
pip install zeep  (Python 3.9+ recommended)
"""

from datetime import datetime
from typing import List, Dict, Any
import sys

from zeep import Client, helpers
from zeep.exceptions import Fault

WSDL_URL = "http://webservices.legis.ga.gov/Legislation/Service.svc?wsdl"

# ----------------- NEW: hard-coded session table ----------------- #
SESSION_ID_TABLE = {
    29: "2025-2026",   # current/active legis session, not yet in SOAP feed
    28: "2023-2024",   
    27: "2021-2022", #current session in SOAP feed
    26: "2019-2020",
    25: "2017-2018",
}

CURRENT_SESSION_ID = 27  #change this when GA IT rolls session 28 and 29 to the SOAP service
# ----------------------------------------------------------------- #

class GALegisClient:
    def __init__(self, wsdl: str = WSDL_URL, timeout: int = 30):
        self.client = Client(wsdl)  # Add custom Transport if proxies/auth are needed
        self.client.settings.strict = False
        self.client.settings.raw_response = False
        self.timeout = timeout

        # ---------- replacement helper -------------- 
    def current_session_id(self) -> int:
        """Return the session Id designated as `current`."""
        return CURRENT_SESSION_ID
    # --------------------------------------------

    # ---------- Core Queries ---------- #
    def search_bills(
        self,
        keywords: str = "safety",
        session_id: int | None = None,
        doc_types: List[str] | None = None,
        page_size: int = 50,
        start_index: int = 0,
        **extra_constraints,
    ) -> Dict[str, Any]:
        """
        Return raw search response (total hits + first page of results).
        Extra SOAP constraints (e.g., SponsorName, Committee) can be passed via **extra_constraints.
        """
        if session_id is None:
            session_id = self.current_session_id()

        # Build constraints object expected by SOAP service
        constraints = {
            "Session": {"Id": session_id},
            "Keywords": keywords,
            "DocumentTypes": (
                [{"DocumentType": dt.upper()} for dt in doc_types] if doc_types else None
            ),
            **extra_constraints,
        }

        try:
            resp = self.client.service.GetLegislationSearchResultsPaged(
                Constraints=constraints,
                PageSize=page_size,
                StartIndex=start_index,
            )
            return helpers.serialize_object(resp, target_cls=dict)
        except Fault as exc:
            raise RuntimeError(
                f"SOAP fault when searching bills: {exc.message}"
                ) from exc

    def bill_detail(
            self, doc_type: str, number: int, session_id: int | None = None
            ) -> Dict[str, Any]:
        if session_id is None:
            session_id = self.current_session_id()
        try:
            resp = self.client.service.GetLegislationDetailByDescription(
                DocumentType=doc_type.upper(),
                Number=number,
                SessionId=session_id
            )

            return helpers.serialize_object(resp, target_cls=dict)
        except Fault as exc:
            raise RuntimeError(
                f"Could not fetch detail for {doc_type} {number}: {exc.message}"
                ) from exc


# ---------------- EXAMPLE USAGE ---------------- #
if __name__ == "__main__":
    ga = GALegisClient()

print("Using session", CURRENT_SESSION_ID, SESSION_ID_TABLE[CURRENT_SESSION_ID])

# 1) Search: X bills (HB/SB) in current session
result = ga.search_bills(
        keywords="safety",#insert keyword
        doc_types=["HB", "SB"],
        page_size=10,
    )

total = result["Total"]
print(f"\nFound {total} matching bills.")

page = result.get("Page")
if not page or not page.get("LegislationSearchResult"):
    print("No bills matched those constraints.")
    sys.exit()

    print("First page:")
    for item in page["LegislationSearchResult"]:
        print(f"• {item['DocumentType']} {item['Number']}: {item['Caption']}")

#for item in result["Page"]["LegislationSearchResult"]:
    #print(f"• {item['DocumentType']} {item['Number']}: {item['Caption']}")

    # 2) Pull full detail for the first returned bill
    first = result["Page"]["LegislationSearchResult"][0]
    detail = ga.bill_detail(first["DocumentType"], first["Number"])

    print(
        f"\n{detail['DocumentType']} {detail['Number']} – {detail['Caption']}\n"
        f"Sponsor: {detail['Sponsor']['MemberDescription']}\n"
        f"Summary: {detail['Summary']}\nStatus history:"
    )
    for status in detail["StatusHistory"]["StatusListing"]:
        print(f"  {status['Date'][:10]} – {status['Description']}")