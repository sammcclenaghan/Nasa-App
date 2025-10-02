# NASA App

Rails 8 application for exploring deterministic "weather risk" probabilities for NASA Space Apps. Users submit latitude, longitude, and a target date; a Sidekiq job invokes the Python model in `lib/weather_model.py` to generate probabilities that are rendered live with Hotwire and can be exported as CSV.

## Stack
- Ruby 3.4.1 (Rails 8.0.3)
- Sidekiq + Redis for background jobs
- MySQL 8 for persistence
- Hotwire (Turbo + Stimulus) for live updates
- Python 3 (NumPy, Pandas, SciPy) for the weather model

## Prerequisites
- macOS/Linux shell with Git, OpenSSL, libyaml, build tools
- Ruby 3.4.1 via `asdf`, `rbenv`, or Ruby installer of choice
- Bundler: `gem install bundler`
- Python 3.10+ with `venv`
- MySQL 8 (or a compatible hosted instance)
- Redis 7
- Node.js is optional; Tailwind assets are built through the `tailwindcss-rails` gem

> If you prefer not to install MySQL/Redis locally, use the Docker Compose workflow described below.

## Local Setup (host machine)
1. Install dependencies above. On macOS with Homebrew:
   ```sh
   brew install mysql redis python@3.12
   brew services start mysql
   brew services start redis
   ```
2. Ensure you have credentials:
   - `config/master.key` should be present; otherwise request it from the team.
   - Create `config/credentials/development.yml.enc` entries as needed (none required by default).
3. Install Ruby gems:
   ```sh
   bundle install
   ```
4. Create a Python virtual environment and install the model dependencies:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   deactivate
   ```
5. Tell Rails which Python interpreter to use. Create a `.env` file (Foreman loads it) with:
   ```sh
   echo "PYTHON_BIN=$(pwd)/.venv/bin/python" >> .env
   ```
   Alternatively export `PYTHON_BIN` in your shell before starting the app.
6. Prepare the database (the default config expects a `root` MySQL user with no password; adjust `config/database.yml` if needed):
   ```sh
   bin/rails db:prepare
   ```
7. Start the development processes (Rails, Tailwind watcher, Sidekiq) via Foreman:
   ```sh
   bin/dev
   ```
   - App: http://localhost:3000
   - Sidekiq dashboard: add a route if desired; logs stream in your terminal

## Docker Compose Workflow
The repo includes a Compose file that provisions the web app, Sidekiq worker, MySQL, and Redis. It is useful for a fully containerized dev environment.

```sh
# Build and start all services
docker compose up --build

# Tail the web logs separately (optional)
docker compose logs -f web
```

Compose specifics:
- `web` serves Rails on http://localhost:3000.
- `worker` runs Sidekiq with `config/sidekiq.yml`.
- `db` (MySQL 8) and `redis` (Redis 7.2) expose ports 3306 and 6379 respectively.
- Python dependencies are installed inside the image; no host-level Python needed.
- Data volumes `db_data` and `redis_data` persist across restarts.

Run `docker compose down --volumes` to wipe data.

## Running Checks
- Unit/system tests: `bin/rails test`
- Lint (Rubocop): `bundle exec rubocop`
- Security scan (Brakeman): `bundle exec brakeman`

## Background Jobs & Python Model
- Jobs enqueue through `WeatherProbabilityJob` and execute in Sidekiq. Ensure Redis is running before starting `bin/dev` or Sidekiq will crash.
- The Python executable is read from `ENV["PYTHON_BIN"]` and defaults to `python3`. Use the `.venv` interpreter to ensure required packages are available.
- You can test the model standalone:
  ```sh
  PYTHONPATH=lib $PYTHON_BIN lib/weather_model.py --lat 28.57 --lon -80.65 --day 42
  ```

## Useful Commands
- `bin/rails console` – load Rails console (respecting `.env` variables)
- `bin/rails db:seed` – seed data (none provided by default)
- `bin/rails routes` – inspect route table (`weather_results` resources plus root)
- `bin/rails tailwindcss:build` – on-demand Tailwind build
- `bundle exec sidekiq -C config/sidekiq.yml` – run Sidekiq manually if not using `bin/dev`

## Troubleshooting
- **MySQL authentication**: Update `config/database.yml` with user/password or supply `DATABASE_URL` if you don’t run MySQL as root without a password.
- **Redis connection errors**: Confirm Redis service is running (`redis-cli ping`).
- **Python module import errors**: Verify `.venv` exists and `PYTHON_BIN` points to it; re-run the `pip install` step.
- **Credentials missing**: Run `bin/rails credentials:edit` with the master key to create environment secrets.

## Deployment Notes
- Use the provided `Dockerfile` for production builds (optimized multi-stage). Example:
  ```sh
  docker build -t nasa_app .
  docker run -p 80:80 -e RAILS_MASTER_KEY=... nasa_app
  ```
- The project includes Kamal configuration under `.kamal/` for container deployment orchestration.
