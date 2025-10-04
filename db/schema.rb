# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.0].define(version: 2025_10_04_201459) do
  create_table "weather_dashboards", charset: "utf8mb4", collation: "utf8mb4_0900_ai_ci", force: :cascade do |t|
    t.string "name", null: false
    t.text "description"
    t.decimal "latitude", precision: 10, scale: 6, null: false
    t.decimal "longitude", precision: 10, scale: 6, null: false
    t.date "start_date", null: false
    t.date "end_date", null: false
    t.json "variables", null: false
    t.json "thresholds"
    t.integer "status", default: 0, null: false
    t.integer "progress", default: 0, null: false
    t.json "timeseries"
    t.json "statistics"
    t.json "threshold_probabilities"
    t.string "cache_key_digest"
    t.string "error_message"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["cache_key_digest"], name: "index_weather_dashboards_on_cache_key_digest"
    t.index ["latitude", "longitude"], name: "index_weather_dashboards_on_latitude_and_longitude"
    t.index ["start_date", "end_date"], name: "index_weather_dashboards_on_start_date_and_end_date"
    t.index ["status"], name: "index_weather_dashboards_on_status"
  end
end
