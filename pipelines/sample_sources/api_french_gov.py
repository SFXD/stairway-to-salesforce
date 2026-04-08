from _collections_abc import Iterator
from typing import Any

import dlt
import requests


@dlt.source(name="french_gov")
def french_gov_source(resource_name: str, postcode: str, sector: str):
    """
    dlt source for the French Government 'Recherche Entreprises' API.

    Note:
        This source is for DEMONSTRATION purposes only.
        To simplify the educational experience, technical filters are
        hardcoded to fetch only the first 25 ACTIVE and PUBLIC companies.

    GDPR Safety:
        The source enforces 'statut_diffusion=P' and explicitly filters
        out "Individual Entrepreneurs" (legal category '1000') directly
        in the code to prevent processing personal data.

    Args:
        resource_name: The name of the generated dlt resource.
        postcode: French postal code filter (e.g., '69002').
        sector: NAF activity section filter (e.g., 'J' for Tech).
    """

    @dlt.resource(name=resource_name, write_disposition="append")
    def fetch_data() -> Iterator[dict[str, Any]]:
        base_url = "https://recherche-entreprises.api.gouv.fr/search"

        # Technical parameters are locked for safety and simplicity
        query_params: dict[str, Any] = {
            "code_postal": postcode,
            "section_activite": sector,
            "etat_administratif": "A",  # Always Active
            "statut_diffusion": "P",  # Always Public
            "per_page": 25,  # Sample size limit
            "page": 1,  # First page only
        }

        response = requests.get(base_url, params=query_params, timeout=30)
        response.raise_for_status()
        results = response.json().get("results", [])

        for item in results:
            if item.get("nature_juridique") == "1000":
                continue
            yield item

    return fetch_data()
