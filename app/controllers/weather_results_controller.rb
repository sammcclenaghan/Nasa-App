require "csv"

class WeatherResultsController < ApplicationController
  helper WeatherResultsHelper
  before_action :set_weather_result, only: [:show]

  def index
    @weather_results = WeatherResult.recent_first
    @weather_result = WeatherResult.new
    @weather_result.query_date = Date.current.to_s
  end

  def new
    @weather_result = WeatherResult.new
    @weather_result.query_date = Date.current.to_s
  end

  def create
    @weather_result = WeatherResult.new(weather_result_params)
    @weather_result.query_date = params[:weather_result][:query_date]
    @weather_result.day_of_year = compute_day_of_year

    if @weather_result.save
      WeatherProbabilityJob.perform_later(@weather_result.id)
      redirect_to weather_results_path, notice: "Weather probability analysis queued."
    else
      render :new, status: :unprocessable_entity
    end
  rescue ArgumentError => e
    @weather_result.errors.add(:base, "Invalid date provided: #{e.message}")
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
    params.require(:weather_result).permit(:lat, :lon)
  end

  def compute_day_of_year
    date = params[:weather_result][:query_date].presence || Date.current.to_s
    Date.parse(date).yday
  end

  def build_csv(weather_result)
    probabilities = weather_result.probabilities_for_chart || {}
    CSV.generate do |csv|
      csv << ["metric", "probability"]
      probabilities.each do |metric, probability|
        csv << [metric, probability]
      end
    end
  end
end
