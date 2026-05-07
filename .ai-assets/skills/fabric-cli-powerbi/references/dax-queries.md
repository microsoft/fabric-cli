# DAX Query Execution

Execute DAX queries against semantic models using the Power BI REST API via Fabric CLI.

## Prerequisites

```bash
# Get model ID
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')
```

## Basic Queries

### Simple EVALUATE

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{"query": "EVALUATE VALUES(Date[Year])"}]
}'
```

### Table Preview

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{"query": "EVALUATE TOPN(100, Sales)"}]
}'
```

### Multiple Queries

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [
    {"query": "EVALUATE VALUES(Date[Year])"},
    {"query": "EVALUATE VALUES(Product[Category])"}
  ]
}'
```

## Aggregation Queries

### SUMMARIZE

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE SUMMARIZE(Sales, Date[Year], \"Total\", SUM(Sales[Amount]))"
  }]
}'
```

### SUMMARIZECOLUMNS

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE SUMMARIZECOLUMNS(Date[Year], Product[Category], \"Revenue\", SUM(Sales[Amount]), \"Qty\", SUM(Sales[Quantity]))"
  }]
}'
```

### ADDCOLUMNS

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE ADDCOLUMNS(VALUES(Product[Category]), \"Total\", CALCULATE(SUM(Sales[Amount])))"
  }]
}'
```

## Filter Queries

### FILTER

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE FILTER(Sales, Sales[Amount] > 1000)"
  }]
}'
```

### CALCULATETABLE

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE CALCULATETABLE(VALUES(Product[Name]), Sales[Year] = 2024)"
  }]
}'
```

### TOPN with Filter

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE TOPN(10, FILTER(Product, Product[Category] = \"Electronics\"), [Total Sales], DESC)"
  }]
}'
```

## Parameterized Queries

### Single Parameter

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE FILTER(Sales, Sales[Year] = @Year)",
    "parameters": [{"name": "@Year", "value": "2024"}]
  }]
}'
```

### Multiple Parameters

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE FILTER(Sales, Sales[Year] >= @StartYear && Sales[Year] <= @EndYear)",
    "parameters": [
      {"name": "@StartYear", "value": "2022"},
      {"name": "@EndYear", "value": "2024"}
    ]
  }]
}'
```

## Advanced Patterns

### Time Intelligence

```bash
# Year-over-Year comparison
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE ADDCOLUMNS(VALUES(Date[Year]), \"Current\", CALCULATE(SUM(Sales[Amount])), \"Previous\", CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR(Date[Date])))"
  }]
}'
```

### Running Total

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE ADDCOLUMNS(VALUES(Date[Month]), \"RunningTotal\", CALCULATE(SUM(Sales[Amount]), FILTER(ALL(Date[Month]), Date[Month] <= EARLIER(Date[Month]))))"
  }]
}'
```

### Distinct Count

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{
    "query": "EVALUATE ROW(\"UniqueCustomers\", DISTINCTCOUNT(Sales[CustomerID]))"
  }]
}'
```

## Query Options

### Include Nulls

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{"query": "EVALUATE VALUES(Customer[Region])"}],
  "serializerSettings": {"includeNulls": true}
}'
```

### Impersonation (RLS Testing)

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{"query": "EVALUATE Sales"}],
  "impersonatedUserName": "user@contoso.com"
}'
```

## Output Processing

### Extract to CSV

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{"query": "EVALUATE SUMMARIZECOLUMNS(Date[Year], \"Total\", SUM(Sales[Amount]))"}]
}' | jq -r '.results[0].tables[0].rows[] | [.[]] | @csv'
```

### Extract to JSON file

```bash
fab api -A powerbi "datasets/$MODEL_ID/executeQueries" -X post -i '{
  "queries": [{"query": "EVALUATE Sales"}]
}' -o /tmp/query-results.json
```

## Limitations

- Maximum query timeout varies by capacity
- Large result sets may be truncated
- Complex queries may hit memory limits
- Some DAX functions not available via REST API
