require "csv"

class WeatherResultsController < ApplicationController
  helper WeatherResultsHelper
  before_action :set_weather_result, only: [ :show ]

  def index
    @weather_results = WeatherResult.recent_first
    @weather_result = WeatherResult.new
    # `date` is not a model attribute on WeatherResult (we store day_of_year).
    # Keep a separate instance variable for the form's date input.
    @query_date = Date.current.to_s
  end

  def new
    @weather_result = WeatherResult.new
    # Use @query_date to populate the form's date field; avoid assigning to a non-existent model attribute.
    @query_date = Date.current.to_s
  end

  def create
    @weather_result = WeatherResult.new(weather_result_params)
    parsed_date = parse_query_date
    # `date` is not a persisted attribute; store the derived day_of_year on the model.
    @weather_result.day_of_year = parsed_date.yday
    # Keep the parsed date available for the form in case of validation errors or re-render.
    @query_date = parsed_date.to_s

    if @weather_result.save
      WeatherProbabilityJob.perform_later(@weather_result.id)
      redirect_to weather_results_path, notice: "Weather probability analysis queued."
    else
      render :new, status: :unprocessable_entity
    end
  rescue ArgumentError => e
    @weather_result.errors.add(:base, "Invalid date provided: #{e.message}")
    # Preserve what the user entered for re-rendering the form
    @query_date = params.dig(:weather_result, :query_date).presence || Date.current.to_s
    render :new, status: :unprocessable_entity
  end

  def show
    respond_to do |format|
      format.json { render json: @weather_result.data || {} }
      format.csv do
        csv = build_csv(@weather_result)
        send_data csv, filename: "weather_result_#{@weather_result.id}.csv"
      end
      format.html { redirect_to weather_results_path(anchor: ActionView::RecordIdentifier.dom_id(@weather_result)) }
    end
  end

  private

  def set_weather_result
    @weather_result = WeatherResult.find(params[:id])
  end

  def weather_result_params
    # Only permit actual model attributes here. We parse the user-provided
    # `:query_date` separately via `parse_query_date` so we should not permit
    # a non-model attribute that would attempt to be mass-assigned.
    params.require(:weather_result).permit(:lat, :lon)
  end

  def parse_query_date
    raw = params.dig(:weather_result, :query_date).presence || Date.current.to_s
    Date.parse(raw)
  end

  def build_csv(weather_result)
    probabilities = weather_result.probabilities_for_chart || {}
    CSV.generate do |csv|
      csv << [ "metric", "probability" ]
      probabilities.each do |metric, probability|
        csv << [ metric, probability ]
      end
    end
  end
end
