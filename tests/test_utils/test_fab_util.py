# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

import pytest

import fabric_cli.utils.fab_util as utils
from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.utils.fab_util import is_valid_guid, is_valid_iso8601_timestamp


def test_dumps():
    """Test the dumps function with various data types."""
    # Test basic JSON serialization
    data = {"key": "value", "number": 42}
    result = utils.dumps(data)
    assert result == '{"key": "value", "number": 42}'

    # Test with indentation
    result = utils.dumps(data, indent=2)
    expected = '{\n  "key": "value",\n  "number": 42\n}'
    assert result == expected

    # Test bytes redaction
    data_with_bytes = {"key": "value", "bytes_data": b"secret"}
    result = utils.dumps(data_with_bytes)
    assert '"__REDACTED__bytes__"' in result
    assert "secret" not in result

    # Test bytearray redaction
    data_with_bytearray = {"key": "value", "bytearray_data": bytearray(b"secret")}
    result = utils.dumps(data_with_bytearray)
    assert '"__REDACTED__bytes__"' in result
    assert "secret" not in result

    # Test non-serializable object raises TypeError
    class NonSerializable:
        pass

    data_with_non_serializable = {"key": "value", "obj": NonSerializable()}
    with pytest.raises(TypeError) as excinfo:
        utils.dumps(data_with_non_serializable)
    assert "Object of type NonSerializable is not JSON serializable" in str(
        excinfo.value
    )


def test_process_nargs():
    arg = "arg"
    result = utils.process_nargs(arg)
    assert result == arg

    arg = ["arg1", "arg2"]
    result = utils.process_nargs(arg)
    assert result == "arg1 arg2"

    arg = ["arg1", "arg2", "arg3"]
    result = utils.process_nargs(arg)
    assert result == "arg1 arg2 arg3"

    arg = []
    result = utils.process_nargs(arg)
    assert result == ""


def test_remove_dotshortcut_from_path_for_onelake():
    path = "path.Shortcut"
    result = utils.remove_dot_suffix(path)
    assert result == "path"

    path = "path.Shortcut.Shortcut"
    result = utils.remove_dot_suffix(path)
    assert result == "path"

    path = "path"
    result = utils.remove_dot_suffix(path)
    assert result == "path"


def test_get_dict_from_params():

    params = []
    result = utils.get_dict_from_params(params)
    assert result == {}

    params = "key1.key2=value2,key1.key3=value3,key4=value4"
    result = utils.get_dict_from_params(params)
    assert result == {"key1": {"key2": "value2", "key3": "value3"}, "key4": "value4"}

    params = "key1.key2=value2,key1.key3=value3,key4=value4,key5.key6.key7=value7"
    result = utils.get_dict_from_params(params, max_depth=3)
    assert result == {
        "key1": {"key2": "value2", "key3": "value3"},
        "key4": "value4",
        "key5": {"key6": {"key7": "value7"}},
    }

    result = utils.get_dict_from_params(params, max_depth=2)
    assert result == {
        "key1": {"key2": "value2", "key3": "value3"},
        "key4": "value4",
        "key5": {"key6.key7": "value7"},
    }

    result = utils.get_dict_from_params(params, max_depth=1)
    assert result == {
        "key1.key2": "value2",
        "key1.key3": "value3",
        "key4": "value4",
        "key5.key6.key7": "value7",
    }

    params = ["key1.key2=value2,key1.key3=value" "with" "spaces,key4=value4"]
    result = utils.get_dict_from_params(params)
    assert result == {
        "key1": {"key2": "value2", "key3": "valuewithspaces"},
        "key4": "value4",
    }

    params = """key1.key1=[1,2,3],key1.key2=["1","2","3"],key1.key3={"key":"value","key2":"value"},key1.key4=value3,key5=value5"""
    result = utils.get_dict_from_params(params)
    assert result == {
        "key1": {
            "key1": "[1,2,3]",
            "key2": '["1","2","3"]',
            "key3": '{"key":"value","key2":"value"}',
            "key4": "value3",
        },
        "key5": "value5",
    }

    params = "desc1=hi,desc2='hi',desc3=\"hi\""
    result = utils.get_dict_from_params(params)
    assert result == {
        "desc1": "hi",
        "desc2": "hi",
        "desc3": "hi",
    }

    # Test space after comma - this tests the regex pattern fix that allows spaces after commas
    params = "key1=value1, key2=value2, key3=value3"
    result = utils.get_dict_from_params(params)
    assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}

    # Test multiple spaces after comma
    params = "key1=value1,  key2=value2,   key3=value3"
    result = utils.get_dict_from_params(params)
    assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}

    # Test mixed spacing (some with spaces, some without)
    params = "key1=value1,key2=value2, key3=value3,  key4=value4"
    result = utils.get_dict_from_params(params)
    assert result == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4",
    }

    # Test with nested keys and spaces
    params = "key1.sub1=value1, key1.sub2=value2, key2=value3"
    result = utils.get_dict_from_params(params)
    assert result == {"key1": {"sub1": "value1", "sub2": "value2"}, "key2": "value3"}

    # Test with complex values and spaces
    params = 'key1={"nested": "value"}, key2=[1,2,3], key3=simple'
    result = utils.get_dict_from_params(params)
    assert result == {"key1": "{nested: value}", "key2": "[1,2,3]", "key3": "simple"}

    # Test tabs and mixed whitespace after comma
    params = "key1=value1,\tkey2=value2,\n key3=value3"
    result = utils.get_dict_from_params(params)
    assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}


def test_merge_dicts():
    dict1 = {"key1": "value1", "key2": {"key1": "value2"}}
    dict2 = {"key2": {"key2": "value2"}, "key3": "value4"}
    result = utils.merge_dicts(dict1, dict2)
    assert result == {
        "key1": "value1",
        "key2": {"key1": "value2", "key2": "value2"},
        "key3": "value4",
    }

    dict1 = {"key1": "value1", "key2": {"key1": "value2"}}
    dict2 = {"key3": {"key2": "value2"}, "key4": "value4"}
    result = utils.merge_dicts(dict1, dict2)
    assert result == {
        "key1": "value1",
        "key2": {"key1": "value2"},
        "key3": {"key2": "value2"},
        "key4": "value4",
    }

    dict1 = {"key1": "value1", "key2": {"key1": "value2"}}
    dict2 = None
    result = utils.merge_dicts(dict1, dict2)
    assert result == {"key1": "value1", "key2": {"key1": "value2"}}

    dict1 = None
    dict2 = {"key2": {"key2": "value2"}, "key3": "value4"}
    result = utils.merge_dicts(dict1, dict2)
    assert result == {"key2": {"key2": "value2"}, "key3": "value4"}

    dict1 = None
    dict2 = None
    result = utils.merge_dicts(dict1, dict2)
    assert result == None

    dict1 = {"key1": "value1", "key2": {"key1": "value2"}}
    dict2 = {}
    result = utils.merge_dicts(dict1, dict2)
    assert result == {"key1": "value1", "key2": {"key1": "value2"}}

    dict1 = {}
    dict2 = {"key2": {"key2": "value2"}, "key3": "value4"}
    result = utils.merge_dicts(dict1, dict2)
    assert result == {"key2": {"key2": "value2"}, "key3": "value4"}


def test_remove_keys_from_dict():
    _dict = {"key1": "value1", "key2": {"key1": "value2"}, "key3": "value3"}
    keys = ["key1"]
    result = utils.remove_keys_from_dict(_dict, keys)
    assert result == {"key2": {"key1": "value2"}, "key3": "value3"}

    _dict = {
        "key1": "value1",
        "key2": {"key1": "value2"},
        "key3": "value3",
        "key4": {"key1": "value4"},
    }
    keys = ["key1"]
    result = utils.remove_keys_from_dict(_dict, keys)
    assert result == {
        "key2": {"key1": "value2"},
        "key3": "value3",
        "key4": {"key1": "value4"},
    }

    _dict = {"key1": "value1", "key2": {"key1": "value2"}}
    keys = ["key3"]
    result = utils.remove_keys_from_dict(_dict, keys)
    assert result == _dict


def test_get_os_specific_command(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Windows")
    result = utils.get_os_specific_command("ls")
    assert result == "dir"

    result = utils.get_os_specific_command("rm")
    assert result == "del"

    result = utils.get_os_specific_command("unknown_command")
    assert result == "unknown_command"

    result = utils.get_os_specific_command("unknown_command")
    assert result == "unknown_command"


def test_get_capacity_settings(monkeypatch):
    _config = {
        fab_constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID: None,
        fab_constant.FAB_DEFAULT_AZ_RESOURCE_GROUP: None,
        fab_constant.FAB_DEFAULT_AZ_LOCATION: None,
        fab_constant.FAB_DEFAULT_AZ_ADMIN: None,
    }

    def mock_get_config(key):
        return _config[key]

    monkeypatch.setattr(fab_state_config, "get_config", mock_get_config)

    with pytest.raises(utils.FabricCLIError) as e:
        utils.get_capacity_settings()

    assert e.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert e.value.message.startswith("Azure subscription ID is not set")

    _config[fab_constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID] = "sub_id"

    with pytest.raises(utils.FabricCLIError) as e:
        utils.get_capacity_settings()

    assert e.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert e.value.message.startswith("Azure resource group is not set")

    _config[fab_constant.FAB_DEFAULT_AZ_RESOURCE_GROUP] = "rg"

    with pytest.raises(utils.FabricCLIError) as e:
        utils.get_capacity_settings()

    assert e.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert e.value.message.startswith("Azure default location is not set")

    _config[fab_constant.FAB_DEFAULT_AZ_LOCATION] = "loc"

    with pytest.raises(utils.FabricCLIError) as e:
        utils.get_capacity_settings()

    assert e.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert e.value.message.startswith("Azure default admin is not set")

    _config[fab_constant.FAB_DEFAULT_AZ_ADMIN] = "admin"

    result = utils.get_capacity_settings()
    assert result == ("admin", "loc", "sub_id", "rg", "F2")

    # Params take precendece over config
    _params = {"subscriptionid": "new_sub_id"}
    result = utils.get_capacity_settings(_params)
    assert result == ("admin", "loc", "new_sub_id", "rg", "F2")

    _params["resourcegroup"] = "new_rg"
    result = utils.get_capacity_settings(_params)
    assert result == ("admin", "loc", "new_sub_id", "new_rg", "F2")

    _params["location"] = "new_loc"
    result = utils.get_capacity_settings(_params)
    assert result == ("admin", "new_loc", "new_sub_id", "new_rg", "F2")

    _params["admin"] = "new_admin"
    result = utils.get_capacity_settings(_params)
    assert result == ("new_admin", "new_loc", "new_sub_id", "new_rg", "F2")


class TestIsValidGuid:
    """Test cases for is_valid_guid function."""

    def test_valid_guid_lowercase(self):
        """Test valid GUID with lowercase letters."""
        assert is_valid_guid("12345678-1234-1234-1234-123456789abc")

    def test_valid_guid_uppercase(self):
        """Test valid GUID with uppercase letters."""
        assert is_valid_guid("12345678-1234-1234-1234-123456789ABC")

    def test_valid_guid_mixed_case(self):
        """Test valid GUID with mixed case letters."""
        assert is_valid_guid("12345678-abcd-ABCD-1234-123456789AbC")

    def test_invalid_guid_wrong_format(self):
        """Test invalid GUID with wrong format."""
        assert not is_valid_guid("not-a-guid")

    def test_invalid_guid_missing_hyphens(self):
        """Test invalid GUID with missing hyphens."""
        assert not is_valid_guid("1234567812341234123412345678abc")

    def test_invalid_guid_extra_characters(self):
        """Test invalid GUID with extra characters."""
        assert not is_valid_guid("12345678-1234-1234-1234-123456789abcd")

    def test_invalid_guid_empty_string(self):
        """Test empty string is not a valid GUID."""
        assert not is_valid_guid("")


class TestIsValidIso8601Timestamp:
    """Test cases for is_valid_iso8601_timestamp function."""

    def test_valid_timestamp_utc_z_suffix(self):
        """Test valid ISO 8601 timestamp with Z suffix."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00Z")

    def test_valid_timestamp_with_milliseconds(self):
        """Test valid ISO 8601 timestamp with milliseconds."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00.123Z")

    def test_valid_timestamp_with_microseconds(self):
        """Test valid ISO 8601 timestamp with microseconds."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00.123456Z")

    def test_valid_timestamp_positive_offset(self):
        """Test valid ISO 8601 timestamp with positive timezone offset."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00+05:30")

    def test_valid_timestamp_negative_offset(self):
        """Test valid ISO 8601 timestamp with negative timezone offset."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00-08:00")

    def test_valid_timestamp_zero_offset(self):
        """Test valid ISO 8601 timestamp with zero offset."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00+00:00")

    def test_invalid_timestamp_no_timezone(self):
        """Test timestamp without timezone is invalid."""
        assert not is_valid_iso8601_timestamp("2024-01-15T10:30:00")

    def test_invalid_timestamp_date_only(self):
        """Test date-only string is invalid."""
        assert not is_valid_iso8601_timestamp("2024-01-15")

    def test_invalid_timestamp_wrong_format(self):
        """Test invalid timestamp format."""
        assert not is_valid_iso8601_timestamp("not-a-timestamp")

    def test_invalid_timestamp_empty_string(self):
        """Test empty string is not a valid timestamp."""
        assert not is_valid_iso8601_timestamp("")
