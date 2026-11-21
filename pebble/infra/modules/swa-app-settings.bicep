param swaName string
param keyVaultName string

resource staticWebApp 'Microsoft.Web/staticSites@2024-11-01' existing = {
  name: swaName
}

// This resource replaces the SWA's whole application-settings set; these two are the only ones in use.
// Values are Key Vault references resolved through the SWA's system-assigned identity.
resource appSettings 'Microsoft.Web/staticSites/config@2024-11-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    GOOGLE_CLIENT_ID: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=google-client-id)'
    GOOGLE_CLIENT_SECRET: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=google-client-secret)'
  }
}
