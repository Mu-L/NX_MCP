"""Tests for feature tree tools."""

from unittest.mock import MagicMock

import pytest

# Import must happen inside each test (or fixture) so that the NXOpen mock
# patches are active when the module-level NXSession is first touched.


@pytest.fixture
def feature_tree_tools(mock_nx):
    """Import feature_tree tools with mocked NX."""
    # Force re-import so the module picks up the mock session
    import importlib
    import nx_mcp.tools.feature_tree as ft

    importlib.reload(ft)
    return ft


# ---------------------------------------------------------------------------
# nx_list_features
# ---------------------------------------------------------------------------

class TestListFeatures:
    def test_returns_empty_when_no_features(self, mock_work_part, feature_tree_tools):
        mock_work_part.Features.ToArray.return_value = []

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_list_features()
        )

        assert result.status == "success"
        assert result.data["features"] == []
        assert result.data["count"] == 0

    def test_returns_feature_list(self, mock_work_part, feature_tree_tools):
        feat1 = MagicMock()
        feat1.Name = "Extrude(1)"
        feat1.FeatureType = "EXTRUDE"
        feat1.Timestamp = "2025-01-01T00:00:00"

        feat2 = MagicMock()
        feat2.Name = "Blend(1)"
        feat2.FeatureType = "BLEND"
        feat2.Timestamp = "2025-01-01T00:01:00"

        mock_work_part.Features.ToArray.return_value = [feat1, feat2]

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_list_features()
        )

        assert result.status == "success"
        assert result.data["count"] == 2
        assert result.data["features"][0]["name"] == "Extrude(1)"
        assert result.data["features"][1]["type"] == "BLEND"

    def test_error_when_no_work_part(self, mock_session, feature_tree_tools):
        mock_session.Parts.Work = None

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_list_features()
        )

        assert result.status == "error"


# ---------------------------------------------------------------------------
# nx_get_feature_info
# ---------------------------------------------------------------------------

class TestGetFeatureInfo:
    def test_finds_feature_case_insensitive(self, mock_work_part, feature_tree_tools):
        feat = MagicMock()
        feat.Name = "Extrude(1)"
        feat.FeatureType = "EXTRUDE"
        feat.Timestamp = "2025-01-01T00:00:00"
        expr = MagicMock()
        expr.Name = "p0"
        expr.Value = 50.0
        feat.GetExpressions.return_value = [expr]

        mock_work_part.Features.ToArray.return_value = [feat]

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_get_feature_info("extrude(1)")
        )

        assert result.status == "success"
        assert result.data["name"] == "Extrude(1)"
        assert result.data["expressions"][0]["name"] == "p0"

    def test_returns_error_with_suggestion_when_not_found(self, mock_work_part, feature_tree_tools):
        feat = MagicMock()
        feat.Name = "Extrude(1)"
        mock_work_part.Features.ToArray.return_value = [feat]

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_get_feature_info("nonexistent")
        )

        assert result.status == "error"
        assert result.error_code == "NX_NOT_FOUND"
        assert "Extrude(1)" in result.suggestion


# ---------------------------------------------------------------------------
# nx_get_bounding_box
# ---------------------------------------------------------------------------

class TestGetBoundingBox:
    def test_returns_bounding_box_for_first_body(self, mock_work_part, feature_tree_tools):
        body = MagicMock()
        body.Name = "Body(1)"
        body.GetBoundingBox.return_value = (0.0, 0.0, 0.0, 10.0, 20.0, 30.0)

        mock_work_part.Bodies.ToArray.return_value = [body]

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_get_bounding_box()
        )

        assert result.status == "success"
        assert result.data["body"] == "Body(1)"
        assert result.data["min"] == {"x": 0.0, "y": 0.0, "z": 0.0}
        assert result.data["max"] == {"x": 10.0, "y": 20.0, "z": 30.0}
        assert result.data["dimensions"]["length_x"] == 10.0
        assert result.data["dimensions"]["length_y"] == 20.0
        assert result.data["dimensions"]["length_z"] == 30.0

    def test_finds_named_body(self, mock_work_part, feature_tree_tools):
        body1 = MagicMock()
        body1.Name = "Body(1)"
        body2 = MagicMock()
        body2.Name = "MyBody"
        body2.GetBoundingBox.return_value = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)

        mock_work_part.Bodies.ToArray.return_value = [body1, body2]

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_get_bounding_box("mybody")
        )

        assert result.status == "success"
        assert result.data["body"] == "MyBody"
        assert result.data["dimensions"]["length_x"] == 3.0

    def test_error_when_no_bodies(self, mock_work_part, feature_tree_tools):
        mock_work_part.Bodies.ToArray.return_value = []

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_get_bounding_box()
        )

        assert result.status == "error"
        assert result.error_code == "NX_NOT_FOUND"

    def test_error_when_named_body_not_found(self, mock_work_part, feature_tree_tools):
        body = MagicMock()
        body.Name = "Body(1)"
        mock_work_part.Bodies.ToArray.return_value = [body]

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            feature_tree_tools.nx_get_bounding_box("missing")
        )

        assert result.status == "error"
        assert "Body(1)" in result.suggestion
