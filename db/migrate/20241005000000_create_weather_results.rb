class CreateWeatherResults < ActiveRecord::Migration[8.0]
  def change
    create_table :weather_results do |t|
      t.decimal :lat, precision: 10, scale: 6, null: false
      t.decimal :lon, precision: 10, scale: 6, null: false
      t.integer :day_of_year, null: false
      t.integer :status, null: false, default: 0
      t.json :data
      t.string :error_message

      t.timestamps
    end

    add_index :weather_results, [:lat, :lon, :day_of_year], name: "index_weather_results_on_coordinates_and_day"
  end
end
