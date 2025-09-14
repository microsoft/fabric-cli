# Authentication Examples

This page demonstrates various authentication methods available in the Fabric CLI. Authentication is the first step for accessing Microsoft Fabric resources.


To explore all authentication commands and their parameters, run:

```
fab auth -h
```

---


## Login

### Interactive User Authentication

Log in to Fabric CLI using interactive login with user credentials. The CLI manages the refresh token automatically.


```
fab auth login
? How would you like to authenticate Fabric CLI? Interactive with a web browser
```


### Service Principal Authentication

!!! info "Requires 'Allow service principals to use Fabric APIs' tenant switch to be enabled in the admin portal"

#### Service Principal with Secret

Log in using service principal authentication in interactive mode

```
fab auth login
? How would you like to authenticate Fabric CLI? Service principal authentication with secret
```

Log in using service principal and client secret directly from command line

```
fab auth login -u <client_id> -p <client_secret> --tenant <tenant_id>
```


#### Service Principal with Certificate

Log in using service principal authentication with certificate in interactive mode

```
fab auth login
? How would you like to authenticate Fabric CLI? Service principal authentication with certificate
```

Log in using service principal with certificate that doesn't require a password

```
fab auth login -u <client_id> --certificate /path/to/certificate.pem --tenant <tenant_id>
```

Log in using service principal with password-protected certificate

```
fab auth login -u <client_id> --certificate /path/to/certificate.p12 -p <certificate_password> --tenant <tenant_id>
```

#### Service Principal with Federated Credential

Log in using service principal with federated credential in interactive mode

```
fab auth login
? How would you like to authenticate Fabric CLI? Service principal authentication with federated credential
```

Log in using service principal with federated credential directly

```
fab auth login -u <client_id> --federated-token <token> --tenant <tenant_id>
```

### Managed Identity Authentication

!!! info "Requires 'Allow service principals to use Fabric APIs' tenant switch must be enabled"
!!! info "Currently tested and validated only on Azure Virtual Machine resources"

#### Log in using managed identity in interactive mode

```
fab auth login
? How would you like to authenticate Fabric CLI? Managed identity authentication
```

#### Log in using system assigned managed identity

```
fab auth login --identity
```

#### Log in using user assigned managed identity with specific client ID

```
fab auth login --identity -u <client_id>
```


## Logout

Log out of the current Fabric CLI session and clear authentication tokens

```
fab auth logout
```


## Authentication Status

### View the current authentication state and active account information

```
fab auth status
```


## CI/CD Pipeline Examples

For practical implementations of federated credential authentication:

- **GitHub Actions:** See [GitHub workflow example](./files/github-workflow.yml)
- **Azure DevOps:** See [Azure pipeline example](./files/azure-pipeline.yml)
