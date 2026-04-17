output "app_service_url" {
  value       = "https://${azurerm_linux_web_app.chatbot.default_hostname}"
  description = "Public URL of the chatbot API — use this as VITE_CHATBOT_API_URL in personalweb"
}

output "app_service_name" {
  value       = azurerm_linux_web_app.chatbot.name
  description = "App Service name — needed for the AZURE_WEBAPP_NAME GitHub Actions variable"
}

output "publish_profile_command" {
  value       = "az webapp deployment list-publishing-profiles --name ${azurerm_linux_web_app.chatbot.name} --resource-group ${azurerm_resource_group.chatbot.name} --xml"
  description = "Run this command to get the publish profile XML for the AZURE_WEBAPP_PUBLISH_PROFILE GitHub secret"
}
