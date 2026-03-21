import io
from _collections_abc import Iterable
from typing import Any

import pandas as pd
from dlt.common.typing import TDataItem


def process_csv_result(chunk: Any) -> Iterable[TDataItem]:
    """
    Process a chunk of results from Salesforce Bulk API.
    """
    df: pd.DataFrame = pd.DataFrame()
    # Handle different chunk types from Bulk API
    if isinstance(chunk, str):
        # CSV string response
        try:
            df = pd.read_csv(io.StringIO(chunk))
        except Exception as e:
            raise ValueError(f"Failed to parse CSV chunk: {str(e)}") from e
    elif isinstance(chunk, list):
        # List of dictionaries response
        if chunk:
            df = pd.DataFrame(chunk)
    else:
        raise ValueError(
            f"Unexpected chunk type: {type(chunk).__name__}. Expected str (CSV) or list (records)"
        )
    return df
