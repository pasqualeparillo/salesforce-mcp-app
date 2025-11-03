import uvicorn
from fastapi import FastAPI
from routes.v1 import tools as v1_tools

# Initialize the main FastAPI app
app = FastAPI(
    title="Salesforce MCP Server",
    description="An MCP server for querying live Salesforce data."
)

# Include the router from your tools file.
# This makes your tools available at /api/v1/mcp
app.include_router(v1_tools.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Salesforce MCP Server is running. See /docs for API info."}

# Main entrypoint to run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)