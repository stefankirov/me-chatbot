terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "chatbot" {
  name     = var.resource_group_name
  location = var.location

  lifecycle {
    ignore_changes = [location]
  }
}

resource "azurerm_service_plan" "chatbot" {
  name                = var.app_service_plan_name
  resource_group_name = azurerm_resource_group.chatbot.name
  location            = azurerm_resource_group.chatbot.location
  os_type             = "Linux"
  sku_name            = "F1"

  lifecycle {
    ignore_changes = [location]
  }
}

resource "azurerm_linux_web_app" "chatbot" {
  name                = var.app_service_name
  resource_group_name = azurerm_resource_group.chatbot.name
  location            = azurerm_resource_group.chatbot.location
  service_plan_id     = azurerm_service_plan.chatbot.id
  https_only          = true

  site_config {
    # always_on is not supported on the F1 free tier
    always_on = false

    application_stack {
      python_version = "3.12"
    }

    # Gunicorn + Uvicorn worker for async FastAPI support
    app_command_line = "gunicorn -w 2 -k uvicorn.workers.UvicornWorker asgi:app --timeout 120 --bind 0.0.0.0:8000"
  }

  app_settings = {
    # Triggers Oryx to pip install requirements.txt on each deploy
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"

    # App configuration — sourced from terraform.tfvars (never commit that file)
    "OPENAI_API_KEY"   = var.openai_api_key
    "EMAIL_SMTP_HOST"  = var.email_smtp_host
    "EMAIL_SMTP_PORT"  = tostring(var.email_smtp_port)
    "EMAIL_SENDER"     = var.email_sender
    "EMAIL_PASSWORD"   = var.email_password
    "EMAIL_RECIPIENT"  = var.email_recipient
    "CORS_ORIGINS"      = var.cors_origins
    "PROFILE_CONTENT"   = var.profile_content
    "CHATBOT_API_KEY"   = var.chatbot_api_key
  }

  lifecycle {
    ignore_changes = [location]
  }
}
