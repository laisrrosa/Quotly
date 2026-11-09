package com.quotly.analytics;

public class SimulationResponse {
    private String ticker;
    private double initialAmount;
    private double monthlyContribution;
    private int months;
    private double annualRatePercent;
    private double totalInvested;
    private double totalInterest;
    private double finalBalance;

    public SimulationResponse(String ticker, double initialAmount, double monthlyContribution,
                              int months, double annualRatePercent, double totalInvested,
                              double totalInterest, double finalBalance) {
        this.ticker = ticker;
        this.initialAmount = initialAmount;
        this.monthlyContribution = monthlyContribution;
        this.months = months;
        this.annualRatePercent = annualRatePercent;
        this.totalInvested = totalInvested;
        this.totalInterest = totalInterest;
        this.finalBalance = finalBalance;
    }

    public String getTicker() { return ticker; }
    public double getInitialAmount() { return initialAmount; }
    public double getMonthlyContribution() { return monthlyContribution; }
    public int getMonths() { return months; }
    public double getAnnualRatePercent() { return annualRatePercent; }
    public double getTotalInvested() { return totalInvested; }
    public double getTotalInterest() { return totalInterest; }
    public double getFinalBalance() { return finalBalance; }
}
