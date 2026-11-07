param location string
param tags object
param swaName string

resource staticWebApp 'Microsoft.Web/staticSites@2024-11-01' = {
  name: swaName
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {}
}

output swaId string = staticWebApp.id
output swaName string = staticWebApp.name
output defaultHostname string = staticWebApp.properties.defaultHostname
