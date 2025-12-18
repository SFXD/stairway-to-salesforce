from typing import Set
import logging
import pandas as pd
from simple_salesforce import SalesforceError, SalesforceResourceNotFound, SalesforceMalformedRequest
from dlt_salesforce_advanced.utils.salesforce_validators import (
    sanitize_sobject_name,
    sanitize_field_name
)
from dlt_salesforce_advanced.utils.salesforce_api_helper import process_csv_result

logger = logging.getLogger(__name__)

class SalesforceRepository:
    
    def _build_query(
        self,
        sobject: str,
        key_field: str,
        key_values: Set[str] = None
    ) -> str:
        """
        Build base SOQL query, used both or a full load and a filtered load 
        
        Args:
            sobject: Salesforce object name
            key_field: External key field name
        
        Returns:
            SOQL query string
        """
        # Validate inputs (prevents injection attacks)
        validated_sobject = sanitize_sobject_name(sobject)
        validated_key_field = sanitize_field_name(key_field,allow_relationship_notation=False)

        base_query = (
            f"SELECT Id, {validated_key_field} "
            f"FROM {validated_sobject} "
            f"WHERE {validated_key_field} != null"
        )

        filter_query =""
        if key_values:
            # Escape single quotes in values (prevents injection)
            escaped_keys = [str(key).replace("'", "\\'") for key in key_values]
            formatted_keys = ", ".join(f"'{key}'" for key in escaped_keys)
            filter_query = ( f" AND {key_field} IN ({formatted_keys})" )

        return (f"{base_query}{filter_query}")
    
    def fetch_all(
        self,
        salesforce_driver,
        sobject: str,
        key_field: str
    ) -> pd.DataFrame:
        """
        fetch mapping for the given sobject, using the Bulk API v2
        
        Args:
            salesforce_driver: driver for salesforce
            sobject: Salesforce object name
            key_field: External key field name
        
        Returns:
            DataFrame with Id and key_field columns
        """      
        all_data = []
        id_field = "Id"
        soql =  self._build_query(sobject,key_field)

        try:
            bulk_handler = getattr(salesforce_driver.bulk2, sobject)
            for chunk in bulk_handler.query(soql):         
                df_chunk= process_csv_result(chunk)
                all_data.append(df_chunk)
        except SalesforceResourceNotFound as ne:
            logger.error(f"Invalid sobject name : {sobject}, exception={ne}")
            raise
        except SalesforceMalformedRequest as me:
            logger.error(f"Malformed soql query: '{soql}', exception={me}")
            raise

        if not all_data:
            df= pd.DataFrame(columns=[id_field, key_field])
        else:
            # Combine all chunk
            df = pd.concat(list(all_data), ignore_index=True)  
                                            
        return df[[id_field, key_field]]
            

    
    def fetch_with_keys(
        self,            
        salesforce_driver,
        sobject: str,
        key_field: str,
        key_values: Set[str]
    ) -> pd.DataFrame:
        """
        fetch mapping for specific keys for the specific sobject using the REST API
        raise an error for more than 400 key values ( due to SOQL query length limit )
        
        Args:
            salesforce_driver: driver for salesforce
            sobject: Salesforce object name
            key_field: External key field name
            key_values: key_values to load
        
        Returns:
            DataFrame with Id and key_field columns
        """
        # Convert set to list for batching
        key_list = list(key_values)
        if len(key_list) > 400:
            raise ValueError(f"Error: fetch_with_keys can handle up to 400 filter values ( current = {len(key_list)})")
        
        df_result= pd.DataFrame(columns=["Id", key_field])        
        soql =  self._build_query(sobject,key_field)
        
        try:
            rest_handler = getattr(salesforce_driver.bulk2, sobject)
            results = list(rest_handler.query_all(soql))
            df_all = [process_csv_result(csv_str) for csv_str in results]
            df_result = pd.concat(df_all, ignore_index=True)
        
        except SalesforceResourceNotFound as ne:
            logger.error(f"Invalid sobject name : {sobject}, exception={ne}")
            raise
        except SalesforceMalformedRequest as me:
            logger.error(f"Malformed soql query: '{soql}', exception={me}")
            raise

        return df_result    