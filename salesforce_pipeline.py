    
#!/usr/bin/env python3
"""Pipeline to load Salesforce data."""
import dlt
from sources.salesforce_bulk2 import build_resource

def load() -> None:
    
    """ Configure """    
    pipeline_name = "sync-accounts-test3"

    source_sobject = "Account"
    source_fields=["Id", "Name", "LastModifiedDate", "Description", "CreatedDate", "Active__c",	"Number_of_Contacts__c", "CurrencyIsoCode", "Website", "Match_Billing_Address__c" , "Owner.Name" ]
    source_replication_key = "LastModifiedDate"
    source_filter = None

    write_disposition = "merge"
    field_aliases={ "Id": "account_id", 
                    "Name": "account_name", 
                    "LastModifiedDate": "sf_modification_date",
                    "Owner.Name": "sf_owner"}

    target_destination = 'postgres'
    target_schema = "public"
    target_table_name = "tb_accounts"
    target_primary_key = "account_id"
    target_columns ={"website": {"data_type": "text"}}


    """run the pipeline"""    
    ressource_sobject =  build_resource( target_name=target_table_name, target_primary_key=target_primary_key, 
                                source_sobject=source_sobject, source_fields=source_fields, field_aliases=field_aliases, source_filter=source_filter,
                                write_disposition=write_disposition, source_replication_key= source_replication_key )
    #ressource_sobject.add_map(format_columns)        
    pipeline = dlt.pipeline(pipeline_name=pipeline_name, destination=target_destination, dataset_name=target_schema, 
                            import_schema_path="schemas/import", export_schema_path="schemas/export")
    load_info = pipeline.run([ressource_sobject])
    print(load_info)

if __name__ == "__main__":
    load()