# Analyze Semantic Model

Analyze the semantic model **${input:semanticModelName}** in workspace **${input:workspaceName}**.

## Analysis Steps

### 1. Basic Information
Get the semantic model's metadata:
```
fab get {workspaceName}.Workspace/{semanticModelName}.SemanticModel
```

### 2. Model Definition
Export and inspect the full model definition:
```
fab export {workspaceName}.Workspace/{semanticModelName}.SemanticModel -o ./analysis -f
```

### 3. Table Schema
View the exported TMDL files to inspect tables and columns:
```
# Tables are in: ./analysis/{semanticModelName}.SemanticModel/definition/tables/
```

### 4. Measures
Review measure definitions in the TMDL:
```
# Measures are defined within table TMDL files or a dedicated measures table
```

### 5. Refresh History
Check recent refresh status:
```
fab jobs ls {workspaceName}.Workspace --item-name {semanticModelName}
```

## What to Look For

### Data Quality Issues
- Tables with no relationships (orphaned)
- Missing or incorrect data types
- Large tables that may need partitioning

### Performance Concerns
- Complex calculated columns (consider measures instead)
- Many-to-many relationships
- Large cardinality columns

### Best Practice Violations
- Measures not in a dedicated measures table
- Inconsistent naming conventions
- Missing descriptions on tables/columns

## Output Format

Provide a summary including:
1. **Overview** - Model name, size, table count
2. **Schema** - Tables, columns, data types
3. **Calculations** - Measures with complexity assessment
4. **Relationships** - Diagram description
5. **Recommendations** - Optimization suggestions
