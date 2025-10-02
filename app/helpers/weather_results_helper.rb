module WeatherResultsHelper
  def status_badge_classes(status)
    case status.to_sym
    when :completed
      "bg-green-100 text-green-800"
    when :failed
      "bg-red-100 text-red-800"
    when :processing
      "bg-yellow-100 text-yellow-800"
    else
      "bg-gray-100 text-gray-800"
    end
  end
end
