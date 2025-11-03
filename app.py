import uvicorn
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# --- Setup ---
# Initialize the MCP server with FastAPI integration
mcp = FastMCP(name="salesforce-mcp")

# --- Helper Function to Get Salesforce Connection ---
def get_salesforce_client():
    """
    Fetches credentials from environment variables and returns an
    authenticated simple-salesforce client.
    """
    try:
        # Fetch credentials from environment variables
        sf_user = os.getenv("USERNAME") 
        sf_pass = os.getenv("PASSWORD")
        sf_token = os.getenv("SECURITY_TOKEN")

        if not all([sf_user, sf_pass, sf_token]):
            raise ValueError("Missing required environment variables: USERNAME, PASSWORD, or SECURITY_TOKEN")

        # Authenticate
        sf = Salesforce(
            username=sf_user,
            password=sf_pass,
            security_token=sf_token
        )
        return sf
    except Exception as e:
        print(f"Error connecting to Salesforce: {e}")
        return None

# --- MCP Tool Definitions ---
# We decorate the 'mcp' object directly.
@mcp.tool(
    name="get_user", 
    description="Search the salesforce User object for a specific user.", 
    meta={"version": "1.2", "author": "pat.parillo@catalystcr.com"}
)
async def get_salesforce_account(account_name: str) -> dict:
    """
    Gets live account information directly from Salesforce
    for a given account name.
    """
    sf = get_salesforce_client()
    if not sf:
        return {"status": "error", "message": "Failed to connect to Salesforce"}

    try:
        # Use a SOQL query to find matching accounts
        soql = f"SELECT Id, Name, Industry, Phone, Website FROM Account WHERE Name LIKE '%{account_name}%' LIMIT 5"
        result = sf.query_all(soql)
        
        return {"status": "success", "data": result['records']}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool(
    name="get_contact",
    description="Search the salesforce Contact object for a specific contact.",
    meta={"version": "1.2", "author": "pat.parillo@catalystcr.com"}
)
async def get_salesforce_contact(email: str) -> dict:
    """
    Gets live contact information directly from Salesforce
    for a given email address.
    """
    sf = get_salesforce_client()
    if not sf:
        return {"status": "error", "message": "Failed to connect to Salesforce"}

    try:
        soql = f"SELECT Id, Name, Email, Title, Phone FROM Contact WHERE Email = '{email}' LIMIT 1"
        result = sf.query_all(soql)

        return {"status": "success", "data": result['records']}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# @mcp.tool(
#     name="list_objects",
#     description="Lists all available Salesforce objects (standard and custom) with their basic properties.",
#     meta={"version": "1.0", "author": "pat.parillo@catalystcr.com"}
# )
# async def list_salesforce_objects(custom_only: bool = False) -> dict:
#     """
#     Lists all Salesforce objects available in the org.

#     Args:
#         custom_only: If True, returns only custom objects. Default is False (all objects).
#     """
#     sf = get_salesforce_client()
#     if not sf:
#         return {"status": "error", "message": "Failed to connect to Salesforce"}

#     try:
#         # Get all objects metadata
#         describe = sf.describe()
#         objects = describe['sobjects']

#         # Filter and format the results
#         filtered_objects = []
#         for obj in objects:
#             if custom_only and not obj['custom']:
#                 continue

#             filtered_objects.append({
#                 "name": obj['name'],
#                 "label": obj['label'],
#                 "custom": obj['custom'],
#                 "queryable": obj['queryable'],
#                 "createable": obj['createable'],
#                 "updateable": obj['updateable'],
#                 "deletable": obj['deletable']
#             })

#         return {
#             "status": "success",
#             "count": len(filtered_objects),
#             "data": filtered_objects
#         }

#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool(
#     name="describe_object",
#     description="Gets detailed metadata about a specific Salesforce object including all fields, data types, and relationships.",
#     meta={"version": "1.0", "author": "pat.parillo@catalystcr.com"}
# )
# async def describe_salesforce_object(object_name: str) -> dict:
#     """
#     Gets detailed metadata about a specific Salesforce object.

#     Args:
#         object_name: The API name of the Salesforce object (e.g., 'Account', 'Contact', 'MyCustomObject__c')
#     """
#     sf = get_salesforce_client()
#     if not sf:
#         return {"status": "error", "message": "Failed to connect to Salesforce"}

#     try:
#         # Get object metadata
#         obj_metadata = getattr(sf, object_name).describe()

#         # Format fields information
#         fields = []
#         for field in obj_metadata['fields']:
#             fields.append({
#                 "name": field['name'],
#                 "label": field['label'],
#                 "type": field['type'],
#                 "length": field.get('length'),
#                 "required": not field['nillable'],
#                 "unique": field.get('unique', False),
#                 "createable": field['createable'],
#                 "updateable": field['updateable'],
#                 "referenceTo": field.get('referenceTo', []),
#                 "relationshipName": field.get('relationshipName')
#             })

#         return {
#             "status": "success",
#             "data": {
#                 "name": obj_metadata['name'],
#                 "label": obj_metadata['label'],
#                 "custom": obj_metadata['custom'],
#                 "queryable": obj_metadata['queryable'],
#                 "createable": obj_metadata['createable'],
#                 "updateable": obj_metadata['updateable'],
#                 "deletable": obj_metadata['deletable'],
#                 "fields": fields,
#                 "recordTypeInfos": obj_metadata.get('recordTypeInfos', [])
#             }
#         }

#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool(
#     name="query_object",
#     description="Dynamically queries any Salesforce object with custom filters. Returns records based on the specified criteria.",
#     meta={"version": "1.0", "author": "pat.parillo@catalystcr.com"}
# )
# async def query_salesforce_object(
#     object_name: str,
#     fields: str = "*",
#     where_clause: str = "",
#     limit: int = 10
# ) -> dict:
#     """
#     Queries any Salesforce object with custom filters.

#     Args:
#         object_name: The API name of the Salesforce object (e.g., 'Account', 'Contact')
#         fields: Comma-separated list of fields to retrieve. Use '*' for common fields. Default is '*'.
#         where_clause: Optional WHERE clause (without the WHERE keyword). Example: "Name LIKE '%Acme%' AND IsActive = true"
#         limit: Maximum number of records to return. Default is 10.
#     """
#     sf = get_salesforce_client()
#     if not sf:
#         return {"status": "error", "message": "Failed to connect to Salesforce"}

#     try:
#         # If fields is '*', get common fields
#         if fields == "*":
#             obj_metadata = getattr(sf, object_name).describe()
#             # Get first 10 fields that are queryable and not compound
#             common_fields = []
#             for field in obj_metadata['fields']:
#                 if field['type'] not in ['address', 'location'] and len(common_fields) < 10:
#                     common_fields.append(field['name'])
#             fields = ", ".join(common_fields) if common_fields else "Id"

#         # Build SOQL query
#         soql = f"SELECT {fields} FROM {object_name}"
#         if where_clause:
#             soql += f" WHERE {where_clause}"
#         soql += f" LIMIT {limit}"

#         result = sf.query_all(soql)

#         return {
#             "status": "success",
#             "query": soql,
#             "totalSize": result['totalSize'],
#             "data": result['records']
#         }

#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool(
#     name="get_record",
#     description="Gets a single Salesforce record by its ID from any object.",
#     meta={"version": "1.0", "author": "pat.parillo@catalystcr.com"}
# )
# async def get_salesforce_record(object_name: str, record_id: str) -> dict:
#     """
#     Gets a single record by ID from any Salesforce object.

#     Args:
#         object_name: The API name of the Salesforce object (e.g., 'Account', 'Contact')
#         record_id: The Salesforce record ID (15 or 18 characters)
#     """
#     sf = get_salesforce_client()
#     if not sf:
#         return {"status": "error", "message": "Failed to connect to Salesforce"}

#     try:
#         # Get the record
#         record = getattr(sf, object_name).get(record_id)

#         return {
#             "status": "success",
#             "data": record
#         }

#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# Expose the FastAPI app for uvicorn
mcp_app = mcp.streamable_http_app()

app = FastAPI(
    lifespan=lambda _: mcp.session_manager.run(),
)

app.mount("/", mcp_app)

# --- Main entrypoint (for local testing) ---
if __name__ == "__main__":
    # This runs the 'app' object using uvicorn
    uvicorn.run(
        "app:app",  # import path to your `app`
        host="0.0.0.0",
        port=8000,
        reload=True,  # optional
    )
    # mcp.run(transport='stdio') # used for local development