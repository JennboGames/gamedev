targetScope = 'subscription'

@minLength(1)
@maxLength(64)
param environmentName string

@minLength(1)
param location string

param sessionId string
param deployedBy string
param createdAt string

param resourceGroupName string = 'rg-pebble-dev'

param entraAdminObjectId string
param entraAdminName string
@allowed(['User', 'Group', 'ServicePrincipal'])
param entraAdminType string = 'User'

param postgresVersion string = '16'
param appDbName string = 'foundationdb'
param deploymentContainerName string = 'app-package'

var tags = {
  'app-onboard-skill': 'true'
  'app-onboard-session-id': sessionId
  'created-at': createdAt
  environment: environmentName
  'deployed-by': deployedBy
}

// Names follow prepare-plan.json.naming.resources ({abbreviation}-{environmentName}).
var swaName = 'swa-${environmentName}'
var functionAppName = 'func-${environmentName}'
var planName = 'plan-${environmentName}'
var postgresName = 'psql-${environmentName}'
var storageAccountName = 'st${replace(environmentName, '-', '')}'
var logAnalyticsName = 'log-${environmentName}'
var appInsightsName = 'appi-${environmentName}'

// Pre-existing resource group (not created by this template).
resource rg 'Microsoft.Resources/resourceGroups@2025-04-01' existing = {
  name: resourceGroupName
}

module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: logAnalyticsName
    appInsightsName: appInsightsName
  }
}

module storage './modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    location: location
    tags: tags
    storageAccountName: storageAccountName
    deploymentContainerName: deploymentContainerName
  }
}

module postgres './modules/postgres.bicep' = {
  name: 'postgres'
  scope: rg
  params: {
    location: location
    tags: tags
    pgName: postgresName
    pgVersion: postgresVersion
    appDbName: appDbName
    entraAdminObjectId: entraAdminObjectId
    entraAdminName: entraAdminName
    entraAdminType: entraAdminType
  }
}

module functionApp './modules/function-app.bicep' = {
  name: 'function-app'
  scope: rg
  params: {
    location: location
    tags: tags
    functionAppName: functionAppName
    planName: planName
    storageAccountName: storage.outputs.storageAccountName
    deploymentContainerName: deploymentContainerName
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    postgresHost: postgres.outputs.pgHost
    postgresDatabase: postgres.outputs.appDbName
    // Entra DB role name for the app MI (created post-deploy) equals the Function App name.
    postgresUser: functionAppName
    catalogPath: '/home/site/wwwroot/catalog/products.json'
  }
}

module roleAssignments './modules/role-assignments.bicep' = {
  name: 'role-assignments'
  scope: rg
  params: {
    storageAccountName: storage.outputs.storageAccountName
    functionPrincipalId: functionApp.outputs.principalId
  }
}

module staticWebApp './modules/static-web-app.bicep' = {
  name: 'static-web-app'
  scope: rg
  params: {
    location: location
    tags: tags
    swaName: swaName
  }
}

// Last in dependency order: links /api on the SWA to the Function App.
module swaLinkedBackend './modules/swa-linked-backend.bicep' = {
  name: 'swa-linked-backend'
  scope: rg
  params: {
    swaName: staticWebApp.outputs.swaName
    functionAppId: functionApp.outputs.functionAppId
    backendRegion: location
  }
  dependsOn: [
    roleAssignments
  ]
}

output resourceGroupName string = rg.name
output staticWebAppName string = staticWebApp.outputs.swaName
output staticWebAppHostname string = staticWebApp.outputs.defaultHostname
output functionAppName string = functionApp.outputs.functionAppName
output functionAppHostName string = functionApp.outputs.defaultHostName
output postgresServerName string = postgres.outputs.pgName
output postgresHost string = postgres.outputs.pgHost
output postgresDatabase string = postgres.outputs.appDbName
output storageAccountName string = storage.outputs.storageAccountName
output deploymentContainerName string = deploymentContainerName
