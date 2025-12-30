"""
KDM MCP Client - Python implementation
Connects to KDM MCP Server via SSE transport
"""

import asyncio
import json
import logging
import math
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
            except Exception as e:
                logger.debug(f"[KDM Client] Error during disconnect: {e}")
            finally:
                self._session = None

        if self._sse_context is not None:
            try:
                await self._sse_context.__aexit__(None, None, None)
            except Exception as e:
                logger.debug(f"[KDM Client] Error closing SSE context: {e}")
            finally:
                self._sse_context = None

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

    def _calculate_distance(self, loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
        """
        Calculate distance between two geographic points using Haversine formula

        Args:
            loc1: First location {"lng": float, "lat": float}
            loc2: Second location {"lng": float, "lat": float}

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth radius in kilometers

        lat1, lon1 = math.radians(loc1["lat"]), math.radians(loc1["lng"])
        lat2, lon2 = math.radians(loc2["lat"]), math.radians(loc2["lng"])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def _is_downstream(self, dam_location: Dict[str, float], station_location: Dict[str, float]) -> bool:
        """
        Determine if a station is downstream of a dam

        Simple heuristic: downstream is typically south (lower latitude)
        This works for most Korean rivers which flow north to south

        Args:
            dam_location: Dam location {"lng": float, "lat": float}
            station_location: Station location {"lng": float, "lat": float}

        Returns:
            True if station is downstream (south) of dam
        """
        return station_location["lat"] < dam_location["lat"]

    def _match_by_basin(
        self,
        dam_basin: str,
        direction: str,
        all_facilities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match stations by basin name

        Args:
            dam_basin: Dam's basin name (e.g., "소양강댐하류")
            direction: "downstream" or "upstream"
            all_facilities: List of all facilities to search

        Returns:
            List of matching facilities with match_type="basin"
        """
        if not dam_basin:
            return []

        # Extract base basin name
        # "소양강댐하류" → "소양강댐"
        base_basin = dam_basin.replace("하류", "").replace("상류", "")

        # Construct target basin name based on direction
        if direction == "downstream":
            target_basin = f"{base_basin}하류"
        else:  # upstream
            target_basin = f"{base_basin}상류"

        # Filter facilities by basin
        # Handle nested structure from MCP server
        matches = []
        for facility_result in all_facilities:
            facility = facility_result.get("site", facility_result)
            if facility.get("basin") == target_basin:
                # Create flattened result with match_type
                result = facility.copy()
                result["match_type"] = "basin"
                matches.append(result)

        return matches

    def _geographic_search(
        self,
        dam_location: Dict[str, float],
        direction: str,
        all_facilities: List[Dict[str, Any]],
        max_distance_km: float
    ) -> List[Dict[str, Any]]:
        """
        Search for stations using geographic distance and direction

        Args:
            dam_location: Dam location {"lng": float, "lat": float}
            direction: "downstream" or "upstream"
            all_facilities: List of all facilities to search
            max_distance_km: Maximum distance in kilometers

        Returns:
            List of matching facilities sorted by distance, with distance_km and match_type="geographic"
        """
        candidates = []

        for facility_result in all_facilities:
            # Handle nested structure from MCP server
            facility = facility_result.get("site", facility_result)
            station_loc = facility.get("location")
            if not station_loc:
                continue

            # Calculate distance
            distance = self._calculate_distance(dam_location, station_loc)

            # Filter by maximum distance
            if distance > max_distance_km:
                continue

            # Filter by direction
            is_down = self._is_downstream(dam_location, station_loc)
            if direction == "downstream" and not is_down:
                continue
            if direction == "upstream" and is_down:
                continue

            # Add to candidates
            result = facility.copy()
            result["distance_km"] = round(distance, 2)
            result["match_type"] = "geographic"
            candidates.append(result)

        # Sort by distance
        candidates.sort(key=lambda x: x["distance_km"])

        return candidates

    async def find_related_stations(
        self,
        dam_name: str = None,
        dam_id: int = None,
        direction: str = "downstream",
        station_type: str = "water_level",
        max_distance_km: float = 100.0,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Find upstream or downstream monitoring stations related to a dam

        Uses two strategies:
        1. Basin matching (priority): Find stations in the same watershed
        2. Geographic search (fallback): Find stations by distance and direction

        Args:
            dam_name: Name of the dam (e.g., "소양강댐"). Either dam_name or dam_id required.
            dam_id: Site ID of the dam (e.g., 50548). Either dam_name or dam_id required.
            direction: "downstream" or "upstream"
            station_type: Type of station to find (default: "water_level")
            max_distance_km: Maximum distance for geographic search (default: 100.0)
            limit: Maximum number of results (default: 10)

        Returns:
            Dict with 'dam' info and 'stations' list:
            {
                'dam': {
                    'site_id': 50548,
                    'site_name': '소양강댐',
                    'basin': '소양강댐하류',
                    ...
                },
                'stations': [
                    {'site_id': 1822, 'site_name': '소양강', 'match_type': 'basin', ...},
                    ...
                ]
            }

        Raises:
            ValueError: If dam not found, invalid direction, or neither dam_name nor dam_id provided

        Example:
            >>> client = KDMClient()
            >>> await client.connect()
            >>>
            >>> # Find by dam name
            >>> result = await client.find_related_stations(
            ...     dam_name="소양강댐",
            ...     direction="downstream"
            ... )
            >>> print(f"Dam: {result['dam']['site_name']} (ID: {result['dam']['site_id']})")
            >>> for s in result['stations']:
            ...     print(f"  - {s['site_name']} (ID: {s['site_id']})")
            >>>
            >>> # Find by dam site_id
            >>> result = await client.find_related_stations(
            ...     dam_id=50548,  # 소양강댐
            ...     direction="downstream"
            ... )
        """
        # Step 1: Validate input
        if not dam_name and not dam_id:
            raise ValueError("Either dam_name or dam_id must be provided")

        if direction not in ["upstream", "downstream"]:
            raise ValueError("direction must be 'upstream' or 'downstream'")

        search_key = f"site_id={dam_id}" if dam_id else f"name={dam_name}"
        logger.info(
            f"[find_related_stations] Searching {direction} "
            f"{station_type} stations for dam {search_key}"
        )

        # Step 2: Find dam information
        if dam_id:
            # Search by site_id - search all dams and filter by site_id
            dam_results = await self.search_facilities(
                query="",
                facility_type="dam",
                limit=1000
            )
            dam_results = [r for r in dam_results if r.get("site", r).get("site_id") == dam_id]
            if not dam_results:
                raise ValueError(f"Dam with site_id={dam_id} not found in catalog")
        else:
            # Search by name
            dam_results = await self.search_facilities(
                query=dam_name,
                facility_type="dam",
                limit=5
            )
            if not dam_results:
                raise ValueError(f"Dam '{dam_name}' not found in catalog")

        # Use first result (most relevant match)
        dam_result = dam_results[0]
        dam_info = dam_result.get("site", dam_result)
        dam_basin = dam_info.get("basin")
        dam_location = dam_info.get("location")
        dam_name_for_search = dam_info.get("site_name", dam_name or f"site_{dam_id}")

        logger.debug(
            f"Dam info: basin={dam_basin}, location={dam_location}"
        )

        # Step 3 & 4: Try basin matching first
        stations = []
        if dam_basin:
            # Extract base name for searching
            base_basin = dam_basin.replace("하류", "").replace("상류", "")

            # Search for stations with basin name
            search_query = base_basin.replace("댐", "")  # e.g., "소양강댐" → "소양강"

            all_stations = await self.search_facilities(
                query=search_query,
                facility_type=station_type,
                limit=100
            )

            basin_matches = self._match_by_basin(
                dam_basin, direction, all_stations
            )

            if basin_matches:
                logger.info(
                    f"Basin matching: found {len(basin_matches)} stations"
                )
                stations = basin_matches

        # Step 5: Geographic fallback if basin matching failed
        if not stations and dam_location:
            logger.info("Basin matching failed, using geographic search")

            # Search for nearby stations (use dam name prefix)
            search_prefix = dam_name_for_search.replace("댐", "")[:2]  # Get first 2 chars
            nearby_stations = await self.search_facilities(
                query=search_prefix,
                facility_type=station_type,
                limit=100
            )

            stations = self._geographic_search(
                dam_location, direction, nearby_stations, max_distance_km
            )

            logger.info(
                f"Geographic search: found {len(stations)} stations "
                f"within {max_distance_km}km"
            )

        # Step 6: Handle no results
        if not stations:
            logger.warning(
                f"No {direction} stations found for {dam_name_for_search}"
            )
            if not dam_location:
                logger.warning(
                    f"Dam location data not available, "
                    f"cannot perform geographic search"
                )

        # Step 7: Return with dam info and stations
        return {
            "dam": dam_info,
            "stations": stations[:limit]
        }

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
