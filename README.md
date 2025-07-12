# RuntimeExceptions

A Django-based web application for adding extra data to Strava.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Automated](#automated)
  - [Manual](#manual)
- [Running Tests](#running-tests)
- [Infrastructure](#infrastructure)
- [CSS Pipeline](#css-pipeline)
- [Contributing](#contributing)
- [License](#license)

## Features
- Adds a weather report to your Strava run

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js (for CSS build)
- PostgreSQL or SQLite (default: SQLite)
- Terraform (for infrastructure)

## Installation

### Environment Variables
Set the following environment variables before running the application:
- `STRAVA_CLIENT_ID` (required): Strava API client ID.
- `STRAVA_SECRET` (required): Strava API client secret.
- `STRAVA_KEY` (required): Strava API key.
- `OWM_API_KEY` (required): API key for weather data.

### Automated
If you have make and direnv installed you can `make init` and then `make help`

### Manual
1. **Install Python dependencies:**
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements.dev.txt
   ```
2. **Install Node.js dependencies (for CSS):**
   ```bash
   npm install
   ```
3. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```
4. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## Running Tests

Run all tests using pytest:
```bash
pytest
```

## Infrastructure

Infrastructure is managed with Terraform. See the `infrastructure/` directory for AWS and Cloudflare configuration. Example usage:
```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

## CSS Pipeline

CSS is built using PostCSS. Source files are in `css/`, output is in `static/css/`.
```bash
npm run build:css
```

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[GPLv3](LICENSE)
