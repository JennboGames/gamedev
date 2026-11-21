param storageAccountName string
param functionPrincipalId string
param swaPrincipalId string
param keyVaultName string
param functionSecretNames array
param swaSecretNames array

// Key Vault Secrets User: read secret values, scoped below to individual secrets (least privilege).
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
// Storage Blob Data Owner: host + Flex deployment package + app blobs; also grants generateUserDelegationKey for SAS URLs.
var storageBlobDataOwnerRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
// Reader on the account only: authorizes get_service_properties in the /api/health storage check.
var readerRoleId = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'

resource storage 'Microsoft.Storage/storageAccounts@2026-04-01' existing = {
  name: storageAccountName
}

// Vault and secrets are created outside this template; secret values never enter it.
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource functionSecrets 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = [for name in functionSecretNames: {
  parent: keyVault
  name: name
}]

resource swaSecrets 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = [for name in swaSecretNames: {
  parent: keyVault
  name: name
}]

resource functionSecretReaders 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (name, i) in functionSecretNames: {
  name: guid(functionSecrets[i].id, functionPrincipalId, keyVaultSecretsUserRoleId)
  scope: functionSecrets[i]
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}]

resource swaSecretReaders 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (name, i) in swaSecretNames: {
  name: guid(swaSecrets[i].id, swaPrincipalId, keyVaultSecretsUserRoleId)
  scope: swaSecrets[i]
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: swaPrincipalId
    principalType: 'ServicePrincipal'
  }
}]

resource functionBlobOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, functionPrincipalId, storageBlobDataOwnerRoleId)
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataOwnerRoleId)
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource functionStorageReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, functionPrincipalId, readerRoleId)
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', readerRoleId)
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}
