targetScope = 'resourceGroup'

@description('Project prefix used for Azure resource names.')
param projectName string = 'sentinela'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Service Bus queue that receives clinical alert messages.')
param alertQueueName string = 'clinical-alerts'

@description('Blob container that stores generated reports and evidence envelopes.')
param reportContainerName string = 'sentinela-reports'

var normalizedProject = toLower(replace(projectName, '-', ''))
var uniqueSuffix = uniqueString(resourceGroup().id, projectName)
var storageName = take('${normalizedProject}${uniqueSuffix}', 24)
var serviceBusName = '${projectName}-sb-${uniqueSuffix}'
var keyVaultName = take('${projectName}-kv-${uniqueSuffix}', 24)
var cognitiveName = '${projectName}-ai-${uniqueSuffix}'
var workspaceName = '${projectName}-logs-${uniqueSuffix}'
var appInsightsName = '${projectName}-appi-${uniqueSuffix}'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
  }
}

resource reports 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storage.name}/default/${reportContainerName}'
  properties: {
    publicAccess: 'None'
  }
}

resource serviceBus 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: serviceBusName
  location: location
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource alertQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  name: '${serviceBus.name}/${alertQueueName}'
  properties: {
    lockDuration: 'PT1M'
    maxDeliveryCount: 10
    defaultMessageTimeToLive: 'P14D'
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

resource cognitive 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: cognitiveName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'CognitiveServices'
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: cognitiveName
  }
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
  }
}

output azureRegion string = location
output cognitiveEndpoint string = cognitive.properties.endpoint
output storageAccountName string = storage.name
output storageContainerName string = reportContainerName
output serviceBusNamespace string = serviceBus.name
output serviceBusQueue string = alertQueueName
output keyVaultName string = keyVault.name
output applicationInsightsName string = appInsights.name
