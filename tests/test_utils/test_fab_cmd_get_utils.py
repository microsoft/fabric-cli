# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.utils.fab_cmd_get_utils import should_retrieve_definition


def test_should_retrieve_definition_scenarios():
    """Test the should_retrieve_definition function with various query scenarios."""
    
    # Definition queries should return True (need definition retrieval)
    definition_queries = [
        "definition",
        "definition.parts",
        "definition.content.sql",
        "definition.nested.deeply.property",
    ]
    
    for query in definition_queries:
        result = should_retrieve_definition(query)
        assert result is True, f"Query '{query}' should return True (definition retrieval needed)"
    
    # Full item query should return True (needs definition retrieval)
    assert should_retrieve_definition(".") is True, "Full item query '.' should return True (definition retrieval needed)"
    
    # Empty/None query should return True (full item retrieval includes definition)
    assert should_retrieve_definition("") is True, "Empty query should return True (full item includes definition)"
    assert should_retrieve_definition(None) is True, "None query should return True (full item includes definition)"
    
    # Metadata-only queries should return False (no definition retrieval needed)
    metadata_queries = [
        "properties",
        "properties.connectionString",
        "id",
        "type",
        "displayName",
        "description",
        "workspaceId",
        "folderId",
        "properties.nested.value",
        "displayName.localized",
    ]
    
    for query in metadata_queries:
        result = should_retrieve_definition(query)
        assert result is False, f"Query '{query}' should return False (metadata only, no definition needed)"
    
    # Other non-definition queries should return False
    other_queries = [
        "someField",
        "config.settings",
        "data.values",
        "random",
        "definitionrelated",  # similar but not definition
        "definitions",  # plural, not definition
        "user.definition",  # definition not at root
    ]
    
    for query in other_queries:
        result = should_retrieve_definition(query)
        assert result is False, f"Query '{query}' should return False (no definition retrieval needed)"
    
    # Edge cases with dots and special formatting
    edge_cases = [
        ("definition.", True),    # definition with trailing dot (still needs definition)
        (".definition", False),   # definition not at start (metadata query)
        ("definition..", True),   # definition with double dot (still needs definition)
        ("..definition", False),  # definition not at start (metadata query)
        ("..", False),           # just dots (metadata query)
    ]
    
    for query, expected in edge_cases:
        result = should_retrieve_definition(query)
        assert result == expected, f"Query '{query}' should return {expected}"