class WeatherResult < ApplicationRecord
  attr_accessor :query_date

  enum status: { pending: 0, processing: 1, completed: 2, failed: 3 }

  validates :lat, :lon, :day_of_year, presence: true
  validates :lat, :lon, numericality: true
  validates :day_of_year, numericality: { greater_than_or_equal_to: 1, less_than_or_equal_to: 366 }

  scope :recent_first, -> { order(created_at: :desc) }

  after_create_commit -> { broadcast_prepend_later_to :weather_results, partial: "weather_results/weather_result", locals: { weather_result: self }, target: "weather_results" }
  after_update_commit -> { broadcast_replace_later_to :weather_results, partial: "weather_results/weather_result", locals: { weather_result: self } }

  def probability_payload
    data.presence || {}
  end

  def probabilities_for_chart
    payload = probability_payload
    probabilities_hash = payload.fetch("probabilities", payload)

    probabilities_hash.transform_values do |value|
      value.to_f.round(2)
    end
  end

  def day_of_year_label
    "Day #{day_of_year}"
  end
end
