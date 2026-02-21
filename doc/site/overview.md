# Overview

```mermaid
graph LR
    subgraph DataSource [Data Source]
        Gaspy
        Chorus
        Trademe
        EduCounts[Education Counts]
        Interest
    end

    subgraph DataCollection [Data Collection]
        subgraph GHA [GitHub Actions]
            S_Gaspy[Collect fuel prices]
            S_Chorus[Collect Internet outage map]
        end
        subgraph SH [Self-hosted]
        	S_Trademe[Collect Auckland properties]
        end
        S_schools[Get school information]
        S_interest[Get macroeconomics]
    end

    subgraph Modules [Modules]
        Fuel
        InternetOutage[Internet outage]
        Properties
        Schools
        Macroeconomics
    end

    subgraph Applications [Applications]
        Dashboard[Fuel price dashboard]
    end

    Gaspy --> S_Gaspy --> Fuel --> Dashboard
    Chorus --> S_Chorus --> InternetOutage
    Trademe --> S_Trademe --> Properties
    EduCounts --> S_schools --> Schools
    Interest --> S_interest --> Macroeconomics

    %% Styling
    style DataSource fill:none,stroke:#333,stroke-dasharray: 5 5
    style DataCollection fill:none,stroke:#333,stroke-dasharray: 5 5
    style Modules fill:none,stroke:#333,stroke-dasharray: 5 5
    style Applications fill:none,stroke:#333,stroke-dasharray: 5 5
```

This program majorly has 4 parts.

1.   Data source: Internet locations where I collect data which is helpful for house pricing.
2.   Data collection jobs: Automatic jobs which collect data from data source to Neon database.
3.   Modules: Programs which use one or multiple categories of data and generates independent variables that helps predicting house prices.
4.   Applications: Prediction models or visualization dashboards, which uses the data to generate business values.

