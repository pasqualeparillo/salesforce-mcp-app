import base64
from fastapi import APIRouter
from mcp.server.fastmcp import FastMCP
from simple_salesforce import Salesforce
from databricks.sdk import WorkspaceClient

# --- Setup ---
# Initialize the Databricks client.
# It authenticates automatically when running as a Databricks App.
w = WorkspaceClient()

# Initialize the MCP server and a FastAPI router
mcp = FastMCP()
router = APIRouter()

# --- Helper Function to Get Salesforce Connection ---
def get_salesforce_client():
    """
    Fetches credentials from Databricks Secrets and returns an
    authenticated simple-salesforce client.
    """
    try:
        # Fetch the raw secret response
        user_secret = w.secrets.get_secret(scope="salesforce-creds", key="username")
        pass_secret = w.secrets.get_secret(scope="salesforce-creds", key="password")
        token_secret = w.secrets.get_secret(scope="salesforce-creds", key="security-token")

        # Secrets are base64-encoded. We must decode them.
        sf_user = base64.b64decode(user_secret.value).decode('utf-8')
        sf_pass = base64.b64decode(pass_secret.value).decode('utf-8')
        sf_token = base64.b64decode(token_secret.value).decode('utf-8')

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
@mcp.tool()
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

@mcp.tool()
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

# Mount the MCP server onto this router
router.include_router(mcp.router, prefix="/mcp")