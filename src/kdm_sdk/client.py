"""
KDM MCP Client - Python implementation
Connects to KDM MCP Server via SSE transport
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
except ImportError:
    raise ImportError("MCP SDK not installed. Please install with: pip install mcp")


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Timeout configuration
DEFAULT_TIMEOUT = 30.0  # seconds
CONNECTION_TIMEOUT = 10.0  # seconds


class KDMClient:
    """
    KDM MCP Client for Python

    Provides access to KDM (K-water Data Model) data through MCP protocol.
    Supports SSE (Server-Sent Events) transport.
    """

    def __init__(
        self,
        server_url: str = "http://203.237.1.4:8080/sse",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ):
        """
        Initialize KDM MCP Client

        Args:
            server_url: MCP server SSE endpoint URL
            timeout: Default timeout for operations (seconds)
            max_retries: Maximum number of retry attempts
        """
        self.server_url = server_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[ClientSession] = None
        self._sse_context = None
        self._read_stream = None
        self._write_stream = None
        self._connection_lock = asyncio.Lock()

    def is_connected(self) -> bool:
        """Check if client is connected to MCP server"""
        return self._session is not None

    async def connect(self) -> None:
        """Connect to MCP server via SSE with timeout and retry logic"""
        async with self._connection_lock:
            if self._session is not None:
                logger.info("[KDM Client] Already connected")
                return

            last_error = None

            for attempt in range(self.max_retries):
                try:
                    logger.info(
                        f"[KDM Client] Connecting to: {self.server_url} "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )

                    # Parse URL to get base URL (without /sse)
                    parsed = urlparse(self.server_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"

                    # Use SSE client with timeout
                    self._sse_context = sse_client(url=self.server_url)  # type: ignore
                    self._read_stream, self._write_stream = await asyncio.wait_for(
                        self._sse_context.__aenter__(), timeout=CONNECTION_TIMEOUT  # type: ignore
                    )

                    # Create session
                    self._session = ClientSession(self._read_stream, self._write_stream)  # type: ignore
                    await self._session.__aenter__()

                    # Initialize session with timeout
                    await asyncio.wait_for(
                        self._session.initialize(), timeout=CONNECTION_TIMEOUT
                    )

                    logger.info(
                        f"[KDM Client] Connected successfully to {self.server_url}"
                    )
                    return

                except asyncio.TimeoutError as e:
                    last_error = f"Connection timeout after {CONNECTION_TIMEOUT}s"
                    logger.warning(f"[KDM Client] {last_error}")
                    self._session = None
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(1)  # Wait before retry

                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"[KDM Client] Connection attempt failed: {e}")
                    self._session = None
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(1)  # Wait before retry

            # All retries failed
            error_msg = (
                f"Connection failed after {self.max_retries} attempts: {last_error}"
            )
            logger.error(f"[KDM Client] {error_msg}")
            raise ConnectionError(error_msg)

    async def disconnect(self) -> None:
        """Disconnect from MCP server"""
        if self._session is not None:
            try:
                await self._session.__aexit__(None, None, None)
                self._session = None
            except Exception as e:
                logger.warning(f"[KDM Client] Error during disconnect: {e}")

        if self._sse_context is not None:
            try:
                await self._sse_context.__aexit__(None, None, None)
                self._sse_context = None
            except Exception as e:
                logger.warning(f"[KDM Client] Error closing SSE context: {e}")

        logger.info("[KDM Client] Disconnected")

    async def _call_tool(
        self, name: str, arguments: Dict[str, Any], timeout: Optional[float] = None
    ) -> Any:
        """
        Call MCP tool and return parsed result with timeout

        Args:
            name: Tool name
            arguments: Tool arguments
            timeout: Operation timeout (uses default if not specified)

        Returns:
            Parsed tool result (usually dict or list)

        Raises:
            ConnectionError: If not connected
            TimeoutError: If operation times out
            ValueError: If result parsing fails
        """
        if self._session is None:
            await self.connect()

        assert self._session is not None, "Session should be connected"

        if timeout is None:
            timeout = self.timeout

        try:
            logger.info(
                f"[KDM Client] Calling tool '{name}' with arguments: {arguments}"
            )

            # Call tool with timeout
            result = await asyncio.wait_for(
                self._session.call_tool(name, arguments), timeout=timeout
            )

            logger.debug(f"[KDM Client] Tool '{name}' raw result: {result}")

            # Parse result from MCP response
            # MCP returns CallToolResult with content array
            if hasattr(result, "content") and len(result.content) > 0:
                # First content block should be TextContent with JSON
                content_block = result.content[0]
                if hasattr(content_block, "text"):
                    try:
                        parsed = json.loads(content_block.text)
                        logger.debug(
                            f"[KDM Client] Tool '{name}' parsed result keys: {parsed.keys() if isinstance(parsed, dict) else type(parsed)}"
                        )
                        return parsed
                    except json.JSONDecodeError as e:
                        logger.error(f"[KDM Client] Failed to parse JSON response: {e}")
                        raise ValueError(
                            f"Invalid JSON response from tool '{name}': {e}"
                        )

            logger.warning(f"[KDM Client] Tool '{name}' returned no content")
            return None

        except asyncio.TimeoutError:
            error_msg = f"Tool call '{name}' timed out after {timeout}s"
            logger.error(f"[KDM Client] {error_msg}")
            raise TimeoutError(error_msg)

        except Exception as e:
            logger.error(f"[KDM Client] Tool call failed: {name} - {e}")
            # Reset connection on certain errors
            if "connection" in str(e).lower():
                logger.warning(
                    "[KDM Client] Connection error detected, resetting session"
                )
                self._session = None
            raise

    async def get_water_data(
        self,
        site_name: str,
        facility_type: Optional[str] = None,
        measurement_items: Optional[List[str]] = None,
        time_key: Optional[str] = None,
        days: int = 7,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_comparison: bool = False,
        include_flood: bool = False,
        include_drought: bool = False,
        include_discharge: bool = False,
        include_weather: bool = False,
        include_quality: bool = False,
        include_safety: bool = False,
        include_related: bool = False,
    ) -> Dict[str, Any]:
        """
        Get water data from KDM

        Args:
            site_name: Facility name (e.g., "소양강댐")
            facility_type: Facility type (dam, water_level, rainfall, weather, water_quality)
            measurement_items: List of measurement items (e.g., ["저수율"])
            time_key: Time key (h_1, d_1, mt_1, or "auto" for fallback)
            days: Number of days to query (default: 7)
            start_date: Start date (YYYYMMDD or YYYY-MM-DD)
            end_date: End date (YYYYMMDD or YYYY-MM-DD)
            include_comparison: Include year-over-year comparison
            include_flood: Include flood-related data
            include_drought: Include drought-related data
            include_discharge: Include discharge details
            include_weather: Include weather data
            include_quality: Include water quality data
            include_safety: Include dam safety data
            include_related: Include related facility data

        Returns:
            Dictionary with query results
        """
        # Auto-fallback logic for time_key
        if time_key == "auto":
            # Try in order: h_1 -> d_1 -> mt_1
            for tk in ["h_1", "d_1", "mt_1"]:
                try:
                    args = {
                        "site_name": site_name,
                        "days": days,
                        "time_key": tk,
                    }

                    if facility_type:
                        args["facility_type"] = facility_type
                    if measurement_items:
                        args["measurement_items"] = measurement_items
                    if start_date:
                        args["start_date"] = start_date
                    if end_date:
                        args["end_date"] = end_date

                    # Add boolean flags
                    if include_comparison:
                        args["include_comparison"] = True
                    if include_flood:
                        args["include_flood"] = True
                    if include_drought:
                        args["include_drought"] = True
                    if include_discharge:
                        args["include_discharge"] = True
                    if include_weather:
                        args["include_weather"] = True
                    if include_quality:
                        args["include_quality"] = True
                    if include_safety:
                        args["include_safety"] = True
                    if include_related:
                        args["include_related"] = True

                    result = await self._call_tool("get_kdm_data", args)

                    if result and result.get("success") and result.get("data"):
                        logger.info(
                            f"[KDM Client] Auto-fallback succeeded with time_key: {tk}"
                        )
                        result["used_time_key"] = tk
                        return result

                except Exception as e:
                    logger.debug(
                        f"[KDM Client] Auto-fallback failed for time_key {tk}: {e}"
                    )
                    continue

            # All failed - return last error
            logger.warning("[KDM Client] All auto-fallback attempts failed")
            return {"success": False, "message": "No data found with auto-fallback"}

        # Normal call (no auto-fallback)
        args = {
            "site_name": site_name,
            "days": days,
        }

        if facility_type:
            args["facility_type"] = facility_type
        if measurement_items:
            args["measurement_items"] = measurement_items
        if time_key:
            args["time_key"] = time_key
        if start_date:
            args["start_date"] = start_date
        if end_date:
            args["end_date"] = end_date

        # Add boolean flags
        if include_comparison:
            args["include_comparison"] = True
        if include_flood:
            args["include_flood"] = True
        if include_drought:
            args["include_drought"] = True
        if include_discharge:
            args["include_discharge"] = True
        if include_weather:
            args["include_weather"] = True
        if include_quality:
            args["include_quality"] = True
        if include_safety:
            args["include_safety"] = True
        if include_related:
            args["include_related"] = True

        return await self._call_tool("get_kdm_data", args)

    async def search_facilities(
        self, query: str, facility_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for facilities

        Args:
            query: Search query (facility name)
            facility_type: Filter by facility type
            limit: Maximum number of results

        Returns:
            List of matching facilities
        """
        args = {
            "query": query,
            "limit": limit,
        }

        if facility_type:
            args["facility_type"] = facility_type

        result = await self._call_tool("search_catalog", args)

        # Return results array if available
        if isinstance(result, dict) and "results" in result:
            return result["results"]
        elif isinstance(result, list):
            return result
        else:
            return []

    async def list_measurements(
        self, site_name: str, facility_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available measurements for a facility

        Args:
            site_name: Facility name
            facility_type: Facility type (optional)

        Returns:
            Dictionary with measurement information
        """
        args = {
            "site_name": site_name,
        }

        if facility_type:
            args["facility_type"] = facility_type

        return await self._call_tool("list_measurements", args)

    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            if self._session is None:
                await self.connect()

            assert self._session is not None, "Session should be connected"

            # Ping the server
            await self._session.send_ping()
            return True

        except Exception as e:
            logger.warning(f"[KDM Client] Health check failed: {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
