# frozen_string_literal: true

# Minimal migration: add a visitor_token column (non-unique) plus index.
# You indicated you do not need to preserve or backfill existing data.
# This keeps it simple and leaves any cleanup/reset to separate steps
# (e.g., running `rails db:truncate_all` / `db:reset` or manual deletion).
#
# Note:
# - Column is nullable here to avoid failures if legacy rows exist when migrating.
# - Model-level validation (already added) enforces presence on new records.
# - If you want a NOT NULL constraint later (after ensuring all rows have a value),
#   create a follow-up migration to enforce it.
class AddVisitorTokenToWeatherResults < ActiveRecord::Migration[8.0]
  def change
    add_column :weather_results, :visitor_token, :string
    add_index  :weather_results, :visitor_token
  end
end
