# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for HTTP session reuse in fab_api_client."""


class TestSessionReuse:
    """Test suite for HTTP session reuse."""

    def test_shared_session__returns_same_instance(self):
        """Test that _get_session returns the same session instance."""
        from fabric_cli.client import fab_api_client

        # Reset the shared session
        fab_api_client._shared_session = None

        session1 = fab_api_client._get_session()
        session2 = fab_api_client._get_session()

        assert session1 is session2, "Session should be reused"

        # Clean up
        fab_api_client._shared_session = None
