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
    command = [ python_executable, Rails.root.join("lib", "weather_model.py").to_s,
               "--lat", weather_result.lat.to_f.to_s,
               "--lon", weather_result.lon.to_f.to_s,
               "--datetime", weather_result.datetime.to_s ]

    stdout, stderr, status = Open3.capture3({ "PYTHONPATH" => Rails.root.join("lib").to_s }, *command)

    # Debug output
    Rails.logger.info("Python command: #{command.join(' ')}")
    Rails.logger.info("Python stdout: '#{stdout}'")
    Rails.logger.info("Python stderr: '#{stderr}'")
    Rails.logger.info("Python exit status: #{status.exitstatus}")

    # Check if we got any output
    if stdout.empty?
      raise "Python script produced no output. Stderr: #{stderr}"
    end

    # Parse JSON even if the command failed (Python script now returns JSON on error)
    result = JSON.parse(stdout)
    
    # Check if the result contains an error
    if result["error"]
      raise "Python model failed: #{result['error']}"
    end

    result
  end

  def python_executable
    ENV.fetch("PYTHON_BIN", "python3")
  end
end
