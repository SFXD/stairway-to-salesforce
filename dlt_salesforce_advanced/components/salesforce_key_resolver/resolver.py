"""
Main Salesforce lookup resolver class.
"""
import logging
from typing import Optional, Set, List

from dlt_salesforce_advanced.drivers.salesforce_driver.sfdriver import get_salesforce_driver
from .resolver_cache_manager import CacheManager
from .resolver_data_repository import SalesforceRepository

class SalesforceKeyResolver:
    """
    Utility class for mapping external keys to Salesforce IDs.
    
    Supports two modes:
    1. full_load mode: Load all mappings upfront using Bulk API v2
    2. On-demand mode: Load only required mappings using REST API (more efficient)
    
    The resolver orchestrates cache management and API calls to provide
    fast, efficient ID resolution for DLT pipelines.
    """
    
    def __init__(
        self,        
        credentials: str ="",
    ):
        """
        Initialize the lookup resolver.
        
        Args:
            credentials: Salesforce credentials (SalesforceDriverAuth, dict, or secrets path)
        """
        self.logger=  logging.getLogger("dlt")

        self.cache_manager = CacheManager()
        self.sf_repository = SalesforceRepository()      

        # init the driver if not pass through
        self.sf_driver = get_salesforce_driver(credentials)

    def _load_data(
        self,
        sobject: str,
        key_field: str,
        full_load: bool,
        key_values: Optional[Set[str]] = None
    ) -> int:
        """
        Load an ID mapping for the specified definition (sobject / key field).
        
        This method intelligently determines what data to load:
        - If key_values is None: Full load via Bulk API v2
        - If key_values is provided: Only load missing keys via REST API
        
        Args:
            sobject: Sobject api name
            key_field: Salesforce field api name defined as external id
            key_values: Set of external keys needed (None = load all)
        
        Returns:
            Total number of mappings in cache after loading        
        """        

        # check parameters consistency for a filter load
        if not full_load:
            if not key_values:
                raise ValueError(f"Error: key_values are not defined for a filter load by Salesforce Key Resolver.")
            elif len(key_values) == 0:
                raise ValueError(f"Error: key_values cannot be empty for a filter load by Salesforce Key Resolver.")

        cache_size=0
        try:
            df_new = None
            if full_load:
                df_new= self.sf_repository.fetch_all(self.sf_driver,sobject,key_field)            
            else:
                # Find missing keys (values not already in cache)
                missing_key_values = self.cache_manager.find_missing_keys(sobject,key_field,key_values)            
                if missing_key_values and len(missing_key_values) > 0:                    
                    df_new= self.sf_repository.fetch_with_keys(self.sf_driver,sobject,key_field,missing_key_values)            
            
            cache_size= self.cache_manager.update_cache(sobject,key_field,df_new)     
        except Exception as e:
            self.logger.error(
                f"Error while loading data from Salesforce for "
                f"{sobject}.{key_field}: {e}"
            )
            raise                

        return cache_size
                    

    def set_definition(
        self,
        sobject: str,
        key_field: str,
        full_load: bool = False,
        key_values: List[str] = None        
    ) -> bool:
        """
        Check if a matching definition (sobject / key_field) exists.
        If not, add a specific mapping for an SObject.
        load all mapping data if full_load is set to true
        
        Args:
            sobject: Sobject apiname
            key_field: Salesforce field apiname defined as external id
            full_load: If True, load all data immediately using Bulk API v2
        
        Returns:
            True if successful, False otherwise        
        """
        
        # Initialize cache entry
        if not self.cache_manager.has_cache(sobject, key_field):
            self.cache_manager.initialize_cache(sobject, key_field)
        
        # Full load mode
        if full_load:
            try:
                self._load_data(sobject, key_field,True)
                self.logger.info(
                    f"✓ full_loaded mapping for "
                    f"{sobject}.{key_field}"
                )
            except Exception as e:
                self.logger.error(
                    f"✗ Failed to full_load mapping for "
                    f"{sobject}.{key_field}: {e}"
                )
                return False
        # Targeted load mode
        elif key_values and len(key_values):
            try:
                self._load_data(sobject, key_field, False, key_values=key_values)
                self.logger.info(
                    f"✓ full_loaded mapping for "
                    f"{sobject}.{key_field}"
                )
            except Exception as e:
                self.logger.error(
                    f"✗ Failed to full_load mapping for "
                    f"{sobject}.{key_field}: {e}"
                )
                return False
        # No load defined
        else:  
            self.logger.warning(
                f"Salesforce Key resolution defined without data loading for "
                f"{sobject}.{key_field}: {e}"
            )            

        return True
        
    def try_resolve(
        self,
        sobject: str,
        key_field: str,
        external_value: str
    ) -> str:
        """
        Try to resolve the given external id for the given definition (sobject and key field)
        if not found, return the external_value (to avoid data loss)
        
        Args:
            sobject: Sobject apiname
            key_field: Salesforce field apiname defined as external id
            external_value: External value to resolve
        
        Returns:
            Salesforce ID if resolved, None otherwise
        """
        resolved_id = self.cache_manager.resolve_single(sobject, key_field, external_value)
        return resolved_id if resolved_id else external_value
       
    def clear_cache(
        self,
        sobject: Optional[str] = None,
        key_field: Optional[str] = None
    ) -> None:
        """
        Clear cache entries.
        
        Args:
            sobject: If specified, only clear this object's caches
            key_field: If specified with sobject, clear only this specific mapping
        """
        self.cache_manager.clear(sobject, key_field)