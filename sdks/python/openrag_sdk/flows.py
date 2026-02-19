"""OpenRAG SDK flows client."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import OpenRAGClient


class FlowsClient:
    """Client for Langflow flow operations."""

    def __init__(self, client: "OpenRAGClient"):
        self._client = client

    async def list(self):
        """
        List available Langflow flows.

        Returns:
            FlowListResponse containing flow summaries.
        """
        from .models import FlowListResponse, FlowSummary

        response = await self._client._request("GET", "/api/v1/flows")
        data = response.json()
        flows = [
            FlowSummary(
                id=f.get("id", ""),
                name=f.get("name", ""),
                description=f.get("description", ""),
            )
            for f in data.get("flows", [])
        ]
        return FlowListResponse(flows=flows)

    async def run(
        self,
        flow_name: str,
        prompt: str,
        *,
        global_vars: dict[str, Any] | None = None,
    ):
        """
        Execute a named Langflow flow.

        Args:
            flow_name: Name of the flow to execute.
            prompt: Input prompt for the flow.
            global_vars: Optional global variables to pass to the flow.

        Returns:
            FlowRunResponse with the flow output.
        """
        from .models import FlowRunResponse

        body: dict[str, Any] = {
            "flow_name": flow_name,
            "prompt": prompt,
        }
        if global_vars:
            body["global_vars"] = global_vars

        response = await self._client._request("POST", "/api/v1/flows/run", json=body)
        data = response.json()
        return FlowRunResponse(
            response=data.get("response", ""),
            flow_id=data.get("flow_id", ""),
        )
