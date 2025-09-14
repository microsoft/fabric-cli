# Label Examples

This page demonstrates how to manage sensitivity labels in Microsoft Fabric using the CLI. Sensitivity labels help classify and protect data based on organizational policies and compliance requirements.

To explore all label commands and their parameters, run:

```
fab label -h
```

---

## Label Configuration


To use labels seamlessly, the CLI needs a local `labels.json` file mapping label IDs to names. Create a JSON file with your organization's sensitivity labels.

Labels configuration file example:

```json
{
    "labels": [
        {
            "name": "Public",
            "id": "00000000-0000-0000-0000-000000000001"
        },
        {
            "name": "Internal",
            "id": "00000000-0000-0000-0000-000000000002"
        },
        {
            "name": "Confidential",
            "id": "00000000-0000-0000-0000-000000000003"
        },
        {
            "name": "Highly Confidential",
            "id": "00000000-0000-0000-0000-000000000004"
        },
        {
            "name": "Restricted",
            "id": "00000000-0000-0000-0000-000000000005"
        }
    ]
}
```

### Configure CLI to Use Label Definitions

Set the CLI configuration to point to your local labels definition file.

```
fab config set local_definition_labels /tmp/labels.json
```

## Label Management

### List Local Labels

View all locally configured sensitivity labels and their mappings.

```
fab label list-local
```

### Apply Sensitivity Labels

#### Set Label by Name

Apply a sensitivity label to an item using the label name.

```
fab label set ws1.Workspace/nb1.Notebook -n Confidential
```

#### Force Apply Label

Apply a sensitivity label without confirmation prompts.

```
fab label set ws1.Workspace/dataset.Lakehouse -n "Highly Confidential" -f
```

### Remove Sensitivity Labels

#### Remove Label with Confirmation

Remove a sensitivity label from an item with interactive confirmation.

```
fab label rm ws1.Workspace/nb1.Notebook
```

#### Force Remove Label

Remove a sensitivity label without confirmation prompts.

```
fab label rm ws1.Workspace/temporary-data.Lakehouse -f
```
