# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

import pytest

import fabric_cli.utils.fab_util as utils
from fabric_cli.core import fab_constant, fab_state_config


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
    assert 'secret' not in result
    
    # Test bytearray redaction
    data_with_bytearray = {"key": "value", "bytearray_data": bytearray(b"secret")}
    result = utils.dumps(data_with_bytearray)
    assert '"__REDACTED__bytes__"' in result
    assert 'secret' not in result
    
    # Test non-serializable object raises TypeError
    class NonSerializable:
        pass
    
    data_with_non_serializable = {"key": "value", "obj": NonSerializable()}
    with pytest.raises(TypeError) as excinfo:
        utils.dumps(data_with_non_serializable)
    assert "Object of type NonSerializable is not JSON serializable" in str(excinfo.value)


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



