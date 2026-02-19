"""
Public API v1 Flows endpoints.

Provides access to Langflow flows — listing and execution.
Uses API key authentication.
"""

from starlette.requests import Request
from starlette.responses import JSONResponse

from config.settings import clients
from utils.logging_config import get_logger

logger = get_logger(__name__)


async def list_flows_endpoint(request: Request):
    """
    List available Langflow flows.

    GET /api/v1/flows

    Response:
        {
            "flows": [
                {"id": "...", "name": "...", "description": "..."}
            ]
        }
    """
    try:
        response = await clients.langflow_request("GET", "/api/v1/flows/")

        if response.status_code != 200:
            return JSONResponse(
                {"error": f"Langflow returned HTTP {response.status_code}"},
                status_code=502,
            )

        data = response.json()

        # Langflow returns a list of flow objects directly
        raw_flows = (
            data
            if isinstance(data, list)
            else data.get("flows", data.get("results", []))
        )

        flows = [
            {
                "id": f.get("id", ""),
                "name": f.get("name", ""),
                "description": f.get("description", ""),
            }
            for f in raw_flows
            if isinstance(f, dict)
        ]

        return JSONResponse({"flows": flows})

    except Exception as e:
        logger.error("Failed to list flows", error=str(e))
        return JSONResponse({"error": str(e)}, status_code=500)


async def run_flow_endpoint(request: Request):
    """
    Execute a named Langflow flow.

    POST /api/v1/flows/run

    Request body:
        {
            "flow_name": "openrag_agent",
            "prompt": "What is RAG?",
            "global_vars": {}  // optional
        }

    Response:
        {
            "response": "RAG is...",
            "flow_id": "uuid-..."
        }
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON in request body"}, status_code=400)

    flow_name = body.get("flow_name", "").strip()
    prompt = body.get("prompt", "").strip()

    if not flow_name:
        return JSONResponse({"error": "flow_name is required"}, status_code=400)
    if not prompt:
        return JSONResponse({"error": "prompt is required"}, status_code=400)

    global_vars = body.get("global_vars") or {}

    try:
        # Resolve flow name → ID
        list_response = await clients.langflow_request("GET", "/api/v1/flows/")
        if list_response.status_code != 200:
            return JSONResponse(
                {"error": f"Failed to list flows: HTTP {list_response.status_code}"},
                status_code=502,
            )

        list_data = list_response.json()
        raw_flows = (
            list_data
            if isinstance(list_data, list)
            else list_data.get("flows", list_data.get("results", []))
        )

        flow_id = None
        for f in raw_flows:
            if isinstance(f, dict) and f.get("name", "").lower() == flow_name.lower():
                flow_id = f.get("id")
                break

        if not flow_id:
            available = [f.get("name", "") for f in raw_flows if isinstance(f, dict)]
            return JSONResponse(
                {
                    "error": f"Flow '{flow_name}' not found",
                    "available_flows": available,
                },
                status_code=404,
            )

        # Execute the flow via Langflow run endpoint
        from agent import async_langflow

        langflow_client = clients.langflow_client
        if langflow_client is None:
            return JSONResponse(
                {"error": "Langflow client not initialized"},
                status_code=503,
            )

        response_text, response_id = await async_langflow(
            langflow_client, flow_id, prompt
        )

        return JSONResponse(
            {
                "response": response_text,
                "flow_id": flow_id,
            }
        )

    except Exception as e:
        logger.error("Flow execution failed", error=str(e), flow_name=flow_name)
        return JSONResponse({"error": str(e)}, status_code=500)
