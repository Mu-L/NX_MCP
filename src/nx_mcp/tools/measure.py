"""Measurement tools — distance, angle, and volume measurement on NX parts."""

from __future__ import annotations

import logging

from nx_mcp.nx_session import NXSession
from nx_mcp.response import ToolError, ToolResult
from nx_mcp.tools.registry import mcp_tool

logger = logging.getLogger("nx_mcp")


# ---------------------------------------------------------------------------
# 1. nx_measure_distance
# ---------------------------------------------------------------------------

@mcp_tool(
    name="nx_measure_distance",
    description="Measure the minimum distance between two objects in the work part.",
    params={
        "obj1": {
            "type": "string",
            "description": "Name or handle of the first object.",
            "required": True,
        },
        "obj2": {
            "type": "string",
            "description": "Name or handle of the second object.",
            "required": True,
        },
    },
)
async def nx_measure_distance(obj1: str, obj2: str) -> str:
    """Measure the distance between two objects."""
    try:
        work_part = NXSession.get_instance().require_work_part()

        measure_manager = work_part.MeasureManager

        # Create a distance measurement between the two named objects
        distance_measure = measure_manager.NewDistance(
            work_part.ModelingViews.WorkView,
            obj1,
            obj2,
        )

        distance_value = distance_measure.Value

        return ToolResult.success(
            data={
                "obj1": obj1,
                "obj2": obj2,
                "distance_mm": distance_value,
            },
            message=f"Distance between '{obj1}' and '{obj2}': {distance_value} mm",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()


# ---------------------------------------------------------------------------
# 2. nx_measure_angle
# ---------------------------------------------------------------------------

@mcp_tool(
    name="nx_measure_angle",
    description="Measure the angle between two objects in the work part.",
    params={
        "obj1": {
            "type": "string",
            "description": "Name or handle of the first object.",
            "required": True,
        },
        "obj2": {
            "type": "string",
            "description": "Name or handle of the second object.",
            "required": True,
        },
    },
)
async def nx_measure_angle(obj1: str, obj2: str) -> str:
    """Measure the angle between two objects."""
    try:
        work_part = NXSession.get_instance().require_work_part()

        measure_manager = work_part.MeasureManager

        # Create an angle measurement between the two named objects
        angle_measure = measure_manager.NewAngle(
            work_part.ModelingViews.WorkView,
            obj1,
            obj2,
        )

        angle_value = angle_measure.Value

        return ToolResult.success(
            data={
                "obj1": obj1,
                "obj2": obj2,
                "angle_deg": angle_value,
            },
            message=f"Angle between '{obj1}' and '{obj2}': {angle_value} degrees",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()


# ---------------------------------------------------------------------------
# 3. nx_measure_volume
# ---------------------------------------------------------------------------

@mcp_tool(
    name="nx_measure_volume",
    description="Measure the volume of a body (or all bodies) in the work part. Returns volume in mm3 and cm3.",
    params={
        "body": {
            "type": "string",
            "description": "Name of the body to measure. If omitted, measures all bodies.",
            "required": False,
        },
    },
)
async def nx_measure_volume(body: str | None = None) -> str:
    """Measure the volume of a body or all bodies."""
    try:
        work_part = NXSession.get_instance().require_work_part()

        bodies = work_part.Bodies.ToArray()

        if not bodies:
            return ToolError(
                error_code="NX_NOT_FOUND",
                message="No bodies found in the work part.",
                suggestion="Create a solid body first, e.g. via nx_extrude.",
            ).to_text()

        target_bodies = bodies
        if body is not None:
            # Find the named body
            found = None
            available: list[str] = []
            for b in bodies:
                available.append(b.Name)
                if b.Name == body:
                    found = b
                    break

            if found is None:
                return ToolError(
                    error_code="NX_NOT_FOUND",
                    message=f"Body '{body}' not found.",
                    suggestion=f"Available bodies: {', '.join(available[:30])}",
                ).to_text()

            target_bodies = [found]

        # Compute volumes
        results: list[dict] = []
        total_volume_mm3 = 0.0

        for b in target_bodies:
            mass_props = b.GetMassProperties()
            volume_mm3 = mass_props.Volume
            volume_cm3 = volume_mm3 / 1000.0
            total_volume_mm3 += volume_mm3
            results.append({
                "body": b.Name,
                "volume_mm3": volume_mm3,
                "volume_cm3": volume_cm3,
            })

        data: dict = {"bodies": results}
        if len(target_bodies) > 1:
            data["total_volume_mm3"] = total_volume_mm3
            data["total_volume_cm3"] = total_volume_mm3 / 1000.0

        msg = (
            f"Measured volume of {len(results)} body(ies): "
            f"{total_volume_mm3:.4f} mm3 / {total_volume_mm3 / 1000.0:.4f} cm3"
        )
        return ToolResult.success(data=data, message=msg).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()
