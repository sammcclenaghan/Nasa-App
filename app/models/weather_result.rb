class WeatherResult < ApplicationRecord
  # query_date is now a persisted :date column (see migration); legacy attr_accessor removed

  enum :status, { pending: 0, processing: 1, completed: 2, failed: 3 }

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

    # Determine the base hash containing probability-like values.
    base =
      if payload["probabilities"].is_a?(Hash)
        payload["probabilities"]
      elsif payload["meta"].is_a?(Hash)
        payload["meta"]
      else
        payload
      end

    # Helper to dig out the first numeric leaf from nested structures
    extract_numeric = lambda do |val|
      case val
      when Numeric
        val.to_f
      when String
        begin
          Float(val)
        rescue ArgumentError
          nil
        end
      when Hash
        val.values.lazy.map { |v| extract_numeric.call(v) }.find { |n| n }
      when Array
        val.lazy.map { |v| extract_numeric.call(v) }.find { |n| n }
      else
        nil
      end
    end

    # Map known meta keys to nicer labels
    key_map = {
      "hot_prob"   => "Hot",
      "cold_prob"  => "Cold",
      "too_rainy"  => "Rainy",
      "too_windy"  => "Windy"
    }

    result = {}

    base.each do |k, v|
      label =
        if key_map.key?(k)
          key_map[k]
        elsif k.to_s.end_with?("_prob")
          # Generic *_prob -> turn into human readable (e.g. very_hot_prob -> "Very Hot")
          k.to_s.sub(/_prob\z/, "")
                .tr("_", " ")
                .split
                .map(&:capitalize)
                .join(" ")
        else
          nil
        end
      next unless label
      num = extract_numeric.call(v)
      next unless num
      result[label] = num.round(2)
    end

    # Fallback: if nothing matched the naming patterns, try casting every value
    if result.empty?
      base.each do |k, v|
        num = extract_numeric.call(v)
        next unless num
        result[k.to_s] = num.round(2)
      end
    end

    result
  end

  def day_of_year_label
    "Day #{day_of_year}"
  end
end
