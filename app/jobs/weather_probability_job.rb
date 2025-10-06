require "json"
require "open3"

class WeatherProbabilityJob < ApplicationJob
  queue_as :default

  def perform(weather_result_id)
    weather_result = WeatherResult.find(weather_result_id)
    weather_result.processing!

    payload = fetch_probabilities(weather_result)

    weather_result.update!(status: :completed, data: payload, error_message: nil)
  rescue StandardError => e
    Rails.logger.error("WeatherProbabilityJob failed: #{e.message}\n#{e.backtrace.join("\n")}")
    weather_result&.update(status: :failed, error_message: e.message)
    raise e
  end

  private

  def fetch_probabilities(weather_result)
    # Safely coerce query_date to a YYYY-MM-DD string (Python expects this exact format)
    date_str = begin
      d = weather_result.respond_to?(:query_date) ? weather_result.query_date : nil
      d = Date.parse(d.to_s) unless d.is_a?(Date)
      d.strftime("%Y-%m-%d")
    rescue StandardError
      Date.current.strftime("%Y-%m-%d")
    end

    command = [
      python_executable,
      Rails.root.join("lib", "weather_model.py").to_s,
      "--lat", weather_result.lat.to_f.to_s,
      "--lon", weather_result.lon.to_f.to_s,
      "--datetime", date_str
    ]

    stdout, stderr, status = Open3.capture3({ "PYTHONPATH" => Rails.root.join("lib").to_s }, *command)

    Rails.logger.info("[WeatherProbabilityJob] Python command: #{command.join(' ')}")
    Rails.logger.info("[WeatherProbabilityJob] Exit status: #{status.exitstatus}")
    Rails.logger.info("[WeatherProbabilityJob] STDOUT (#{stdout.bytesize} bytes): #{stdout.truncate(500)}")
    Rails.logger.info("[WeatherProbabilityJob] STDERR (#{stderr.bytesize} bytes): #{stderr.truncate(500)}")

    raw_json = stdout

    if raw_json.strip.empty?
      if stderr.lstrip.start_with?("{")
        raw_json = stderr
      else
        raise "Python script produced no JSON output (exit #{status.exitstatus}). Stderr:\n#{stderr}"
      end
    end

    begin
      result = JSON.parse(raw_json)
    rescue JSON::ParserError => e
      raise "Failed to parse Python output as JSON: #{e.message}. Raw stdout: #{stdout.truncate(300)} | stderr: #{stderr.truncate(300)}"
    end

    if result.is_a?(Hash) && result["error"]
      raise "Python model failed: #{result['error']}"
    end

    result
  end

  def python_executable
    ENV.fetch("PYTHON_BIN", "python3")
  end
end
