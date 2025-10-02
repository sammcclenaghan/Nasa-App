import { Controller } from "@hotwired/stimulus"
import { Chart, registerables } from "chart.js"

Chart.register(...registerables)

export default class extends Controller {
  static targets = ["canvas"]
  static values = {
    probabilities: Object
  }

  connect() {
    this.renderChart()
  }

  disconnect() {
    if (this.chart) {
      this.chart.destroy()
      this.chart = null
    }
  }

  probabilitiesValueChanged() {
    this.renderChart()
  }

  renderChart() {
    if (!this.hasCanvasTarget || !this.hasProbabilitiesValue) return

    const probabilities = this.probabilitiesValue
    const labels = Object.keys(probabilities)
    const values = labels.map((label) => probabilities[label])

    if (this.chart) {
      this.chart.destroy()
    }

    const context = this.canvasTarget.getContext("2d")
    this.chart = new Chart(context, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Probability (%)",
            data: values,
            backgroundColor: "rgba(37, 99, 235, 0.5)",
            borderColor: "rgb(37, 99, 235)",
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => `${value}%`
            },
            max: 100
          }
        }
      }
    })
  }
}
