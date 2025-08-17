from backend.app.services.aggregates import refresh_metric_aggregates

if __name__ == "__main__":
    refresh_metric_aggregates()
    print("metric aggregates refreshed")
