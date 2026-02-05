# Overview

```mermaid
graph LR
    subgraph DataSource [Data Source]
        Gaspy
        Chorus
        Trademe
    end

    subgraph DataCollection [Data Collection]
        subgraph GHA [GitHub Actions]
            S_Gaspy["Crawler: collect #34;gaspy#34;"]
            S_Chorus["Crawler: collect #34;chorus#34;"]
        end
        subgraph SH [Self-hosted]
        	S_Trademe["Crawler: collect #34;trademe#34;"]
        end
    end

    subgraph Modules [Modules]
        Fuel
        InternetOutage[Internet outage]
        Properties
    end

    subgraph Applications [Applications]
        Dashboard[Fuel price dashboard]
    end

    %% Flow 1
    Gaspy --> S_Gaspy --> Fuel --> Dashboard
    
    %% Flow 2
    Chorus --> S_Chorus --> InternetOutage
    
    %% Flow 3
    Trademe --> S_Trademe --> Properties

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

