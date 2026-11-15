package com.quotly.analytics;

public class VariationResponse {
    private String ticker;
    private double currentPrice;
    private double previousClose;
    private double absoluteChange;
    private double percentageChange;
    private String trend;
    private Double distanceToTargetPercent;

    public VariationResponse(
            String ticker,
            double currentPrice,
            double previousClose,
            double absoluteChange,
            double percentageChange,
            String trend,
            Double distanceToTargetPercent
    ) {
        this.ticker = ticker;
        this.currentPrice = currentPrice;
        this.previousClose = previousClose;
        this.absoluteChange = absoluteChange;
        this.percentageChange = percentageChange;
        this.trend = trend;
        this.distanceToTargetPercent = distanceToTargetPercent;
    }

    public String getTicker() { return ticker; }
    public double getCurrentPrice() { return currentPrice; }
    public double getPreviousClose() { return previousClose; }
    public double getAbsoluteChange() { return absoluteChange; }
    public double getPercentageChange() { return percentageChange; }
    public String getTrend() { return trend; }
    public Double getDistanceToTargetPercent() { return distanceToTargetPercent; }
}
