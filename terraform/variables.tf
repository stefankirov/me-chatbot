variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true
}

variable "resource_group_name" {
  description = "Name of the resource group for the chatbot"
  type        = string
  default     = "chatbot-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "canadacentral"
}

variable "app_service_plan_name" {
  description = "Name of the App Service Plan (F1 free tier)"
  type        = string
  default     = "ASP-chatbotrg-9de6"
}

variable "app_service_name" {
  description = "Name of the Azure Web App — must be globally unique (becomes <name>.azurewebsites.net)"
  type        = string
  default     = "me-chatbot"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "email_smtp_host" {
  description = "SMTP host for outgoing email"
  type        = string
  default     = "smtp.gmail.com"
}

variable "email_smtp_port" {
  description = "SMTP port"
  type        = number
  default     = 587
}

variable "email_sender" {
  description = "Email address used to send notifications"
  type        = string
}

variable "email_password" {
  description = "SMTP app password for the sender email account"
  type        = string
  sensitive   = true
}

variable "email_recipient" {
  description = "Email address that receives chatbot notifications"
  type        = string
}

variable "cors_origins" {
  description = "Comma-separated list of allowed CORS origins (e.g. your personalweb URL)"
  type        = string
  default     = "*"
}

variable "profile_content" {
  description = "Full text of your profile/bio — stored as an app setting so profile.txt is not needed in production"
  type        = string
  sensitive   = true
}

variable "chatbot_api_key" {
  description = "Shared secret sent by the frontend as X-API-Key header. Generate any long random string, e.g. openssl rand -hex 32"
  type        = string
  sensitive   = true
}
