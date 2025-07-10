resource "dokku_app" "runtimeexceptions" {
  app_name = "runtimeexceptions"

  domains = ["www.${var.domain}"]

  config = {
    DJANGO_SETTINGS_MODULE = "runtimeexceptions.settings.prod"
    ALLOWED_HOSTS          = "www.${var.domain}"
    BASE_URL               = "https://www.${var.domain}"
    AWS_ACCESS_KEY_ID      = aws_iam_access_key.access_key.id
    AWS_SECRET_ACCESS_KEY  = aws_iam_access_key.access_key.secret

    SMTP_PASS = aws_iam_access_key.access_key.ses_smtp_password_v4
    SMTP_USER = aws_iam_access_key.access_key.id
    SMTP_PORT = "587"
    SMTP_HOST = "email-smtp.${var.aws_region}.amazonaws.com"

    STRAVA_CLIENT_ID = var.strava_client_id
    STRAVA_SECRET = var.strava_secret
    STRAVA_KEY = var.strava_key
    OWM_API_KEY = var.owm_api_key

    SECRET_KEY = var.secret_key
  }

  ports = {
    80 = {
      scheme         = "http"
      container_port = 8000
    }
  }

  deploy = {
    type = "git_repository"
    git_repository = var.git_repository
  }
}

resource "dokku_plugin" "postgres" {
  name = "postgres"
  url  = "https://github.com/dokku/dokku-postgres.git"
}

resource "dokku_postgres" "main_db" {
  service_name = "runtimeexceptions"
  image = "postgres:17.5"

  depends_on = [
    dokku_plugin.postgres
  ]
}

resource "dokku_postgres_link" "runtimeexceptions_db_link" {
  app_name     = dokku_app.runtimeexceptions.app_name
  service_name = dokku_postgres.main_db.service_name
  alias        = "DATABASE"

  depends_on = [
    dokku_plugin.postgres
  ]
}

output "git-remote" {
  value       = "dokku@${var.hosting_domain}:${dokku_app.runtimeexceptions.app_name}"
  description = "Git remote"
  depends_on  = []
}

resource "dokku_plugin" "letsencrypt" {
  name = "letsencrypt"
  url  = "https://github.com/dokku/dokku-letsencrypt.git"
}

resource "dokku_letsencrypt" "runtimeexceptions" {
  app_name = "runtimeexceptions"
  email    = var.email

  depends_on = [
    dokku_app.runtimeexceptions,
    dokku_plugin.letsencrypt
  ]
}

variable "strava_client_id" {
  description = "Strava Client ID"
}

variable "strava_secret" {
  description = "Strava Secret"
}

variable "strava_key" {
  description = "Strava Key"
}

variable "owm_api_key" {
  description = "OWM API Key"
}
