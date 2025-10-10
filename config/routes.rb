Rails.application.routes.draw do
  get "up" => "rails/health#show", as: :rails_health_check

  resources :weather_results, only: [ :index, :new, :create, :show ]

  root "weather_results#index"
end
