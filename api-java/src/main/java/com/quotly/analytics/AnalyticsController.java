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
        if (ticker == null || ticker.trim().isEmpty()) {
            throw new IllegalArgumentException("O código da ação (ticker) não pode ser vazio.");
        }
        if (initialAmount < 0 || monthlyContribution < 0) {
            throw new IllegalArgumentException("Valores de aporte inicial e mensal não podem ser negativos.");
        }
        if (months < 1 || months > 600) {
            throw new IllegalArgumentException("O prazo em meses deve estar entre 1 e 600.");
        }
        if (annualRatePercent < -100) {
            throw new IllegalArgumentException("A taxa anual não pode ser menor que -100%.");
        }

        double monthlyRate = Math.pow(1.0 + (annualRatePercent / 100.0), 1.0 / 12.0) - 1.0;

        double currentBalance = initialAmount;
        double totalInvested = initialAmount;

        for (int i = 1; i <= months; i++) {
            currentBalance = currentBalance * (1.0 + monthlyRate) + monthlyContribution;
            totalInvested += monthlyContribution;
        }

        double roundedFinal = round2(currentBalance);
        double roundedInvested = round2(totalInvested);
        double totalInterest = round2(roundedFinal - roundedInvested);

        return new SimulationResponse(
                ticker.trim().toUpperCase(),
                initialAmount,
                monthlyContribution,
                months,
                annualRatePercent,
                roundedInvested,
                totalInterest,
                roundedFinal
        );
    }

    @GetMapping("/variation")
    public VariationResponse calculateVariation(
            @RequestParam String ticker,
            @RequestParam double currentPrice,
            @RequestParam double previousClose,
            @RequestParam(required = false) Double targetPrice
    ) {
        if (ticker == null || ticker.trim().isEmpty()) {
            throw new IllegalArgumentException("O código da ação (ticker) não pode ser vazio.");
        }
        if (currentPrice <= 0 || previousClose <= 0) {
            throw new IllegalArgumentException("Os preços atual e anterior devem ser maiores que zero.");
        }
        if (targetPrice != null && targetPrice <= 0) {
            throw new IllegalArgumentException("O preço-alvo deve ser maior que zero.");
        }

        double absoluteChange = round2(currentPrice - previousClose);
        double percentageChange = round2(((currentPrice - previousClose) / previousClose) * 100.0);

        String trend = "NEUTRAL";
        if (absoluteChange > 0) {
            trend = "UP";
        } else if (absoluteChange < 0) {
            trend = "DOWN";
        }

        Double distanceToTargetPercent = null;
        if (targetPrice != null) {
            distanceToTargetPercent = round2(((targetPrice - currentPrice) / currentPrice) * 100.0);
        }

        return new VariationResponse(
                ticker.trim().toUpperCase(),
                round2(currentPrice),
                round2(previousClose),
                absoluteChange,
                percentageChange,
                trend,
                distanceToTargetPercent
        );
    }

    private double round2(double value) {
        return Math.round(value * 100.0) / 100.0;
    }
}
