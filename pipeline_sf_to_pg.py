    
#!/usr/bin/env python3
"""Pipeline to load Salesforce data."""
import dlt
from stairway_to_salesforce.sources.salesforce_bulk2 import build_sfbulk2_resource

def execute() -> None:
    """ Pipeline Example From Salesforce To PostGreSQL"""
    
    pipeline_name = "pipeline_sf_to_pg"    
    source_sobject = "Account"
    target_schema = "public"
    target_table_name = "tb_accounts"
    write_disposition = "merge"

    #FIELD MAPPING "Source Field" : "Target Field"
    fields={ "Id"                           : "account_id", 
            "Name"                          : "account_name", 
            "LastModifiedDate"              : "sf_modification_date",
            "Description"                   : "Description",
            "CreatedDate"                   : "CreatedDate",
            "Active__c"                     : "Active__c",
            "Number_of_Contacts__c"         :"Number_of_Contacts__c", 
            "CurrencyIsoCode"               :"CurrencyIsoCode", 
            "Website"                       :"Website", 
            "Match_Billing_Address__c"      :"Match_Billing_Address__c",
            "Owner.Name"                    : "sf_owner"
    }    
    source_replication_key = "LastModifiedDate"                 #Source replication key must exist in fields as key
    target_primary_key = "account_id"                           #Target primary key must exist in fields as value    
    target_column_types ={"website": {"data_type": "text"}}     #To set as minimum, only to fix field type for special fields ( like URL )

    source_query_filter = None                                  #Source query filter that will be added to the SOQL Query after the WHERE  before the Timestamp selection (if incremental)



    """run the pipeline"""    
    ressource_sobject =  build_sfbulk2_resource(    write_disposition=write_disposition,
                                            target_name=target_table_name, target_primary_key=target_primary_key, target_column_types=target_column_types,
                                            source_sobject=source_sobject, fields=fields, source_query_filter=source_query_filter,source_replication_key= source_replication_key,
                                        )       
    pipeline = dlt.pipeline(    pipeline_name=pipeline_name, destination="postgres", dataset_name=target_schema, 
                                import_schema_path=".dlt/schemas/import", export_schema_path=".dlt/schemas/export")    
    load_info = pipeline.run([ressource_sobject])  # schema_contract="freeze"
    print(load_info)

if __name__ == "__main__":
    execute()