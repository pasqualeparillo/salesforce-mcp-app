import uvicorn
import base64
from mcp.server.fastmcp import FastMCP
from simple_salesforce import Salesforce
from databricks.sdk import WorkspaceClient

# --- Setup ---
# Initialize the MCP server. 
# We name it 'app' so uvicorn can find it.
app = FastMCP(name="Salesforce MCP Server")

# Initialize Databricks client
w = WorkspaceClient()

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
# We decorate the 'app' object directly.
@app.tool()
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

@app.tool()
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

# --- Main entrypoint (for local testing) ---
if __name__ == "__main__":
    # This runs the 'app' object using uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)