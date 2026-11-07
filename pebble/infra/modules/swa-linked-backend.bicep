param swaName string
param functionAppId string
param backendRegion string
param linkName string = 'backend1'

resource staticWebApp 'Microsoft.Web/staticSites@2024-11-01' existing = {
  name: swaName
}

resource linkedBackend 'Microsoft.Web/staticSites/linkedBackends@2024-11-01' = {
  parent: staticWebApp
  name: linkName
  properties: {
    backendResourceId: functionAppId
    region: backendRegion
  }
}
