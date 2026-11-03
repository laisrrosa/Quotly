package com.quotly.analytics;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/analytics")
@CrossOrigin(origins = {"http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"})
public class AnalyticsController {

    @GetMapping("/simulate")
    public SimulationResponse simulate(
            @RequestParam(defaultValue = "PETR4") String ticker,
            @RequestParam(defaultValue = "1000.0") double initialAmount,
            @RequestParam(defaultValue = "200.0") double monthlyContribution,
            @RequestParam(defaultValue = "12") int months,
            @RequestParam(defaultValue = "12.0") double annualRatePercent
    ) {
        double monthlyRate = Math.pow(1.0 + (annualRatePercent / 100.0), 1.0 / 12.0) - 1.0;

        double currentBalance = initialAmount;
        double totalInvested = initialAmount;

        for (int i = 1; i <= months; i++) {
            currentBalance = currentBalance * (1.0 + monthlyRate) + monthlyContribution;
            totalInvested += monthlyContribution;
        }

        double roundedFinal = Math.round(currentBalance * 100.0) / 100.0;
        double roundedInvested = Math.round(totalInvested * 100.0) / 100.0;
        double totalInterest = Math.round((roundedFinal - roundedInvested) * 100.0) / 100.0;

        return new SimulationResponse(
                ticker.toUpperCase(),
                initialAmount,
                monthlyContribution,
                months,
                annualRatePercent,
                roundedInvested,
                totalInterest,
                roundedFinal
        );
    }
}
