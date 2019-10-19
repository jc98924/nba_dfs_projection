# Predicting Fantasy Points for DraftKings NBA Daily Fantasy Sports (DFS)

#### Introduction

Using linear regressions, I hoped to create a prediction algorithm for fantasy points that would at least marginally outpace the projections from a DFS site (fantasycruncher.com).

I have been an avid fan of fantasy basketball since 2015. However, I typically play in a season-long H2H league, which is a far different beast. Because fantasy points give a concrete player value, I knew that this would be a perfect application for supervised learning. 

Going into this project, I had two main goals.

- Create a scraping pipeline for all future game logs.
- Aggregate data via player and team level to track statistics and metrics as needed

One design choice I made at the start of this project was to build FantasyCruncher's own projections into my model. This is all information that I would have access to as the season progressed so it made sense for me to incorporate it into my own. I'm sure their team has put in much more work on this than I have so far so I'm definitely willing to use it.

## Process Flow 

### Data Acquisition & Cleaning

Past game logs are readily available for me to download but I wanted to create a pipeline where I could scrape all game logs going forward. I used a combination of BeautifulSoup and Selenium to download 8 tables for each game which tracks everything from basic statistics like points scored to more advanced ones such as player on-court speed. Note that I did not use a majority of these statistics in my analysis but they will be available for use anytime a new feature needs to be built out. 

I also used Selenium to go through FantasyCruncher and download all of their .csv files for their projections last season. The code is shown in the [**data_collection.ipynb**](https://github.com/jc98924/nba_dfs_projection/blob/master/data_collection.ipynb) file with any functions called from the [**nba_stats_scraper.py**](https://github.com/jc98924/nba_dfs_projection/blob/master/stats_nba_scraper.py) file. 

The bulk of this project was cleaning, merging, and aggregating the game logs on both an individual and team level.

### EDA

Going into this, I knew that DFS would be a very different game. Just for a quick point of reference, H2H leagues are typically scored on 9 categories but efficiency is accounted for. A player that may score you a ton of points may also get you a lot of turnovers so it's a constant balance you need to walk depending on your team needs. Let's take a quick look at the DraftKings scoring model. 

#### DraftKings Scoring Breakdown

| Metric        | Point Value |
| ------------- | ----------- |
| Point         | + 1.00 Pts  |
| Made 3pt Shot | + 0.50 Pts  |
| Rebound       | + 1.25 Pts  |
| Assist        | + 1.50 Pts  |
| Steal         | + 2.00 Pts  |
| Block         | + 2.00 Pts  |
| Turnover      | - 0.50 Pts  |
| Double-double | + 1.50 Pts  |
| Triple-double | + 3.00 Pts  |

Unlike standard 9-cat H2H leagues, efficiency metrics such as FG% and FT% aren't factors and turnovers have a marginal impact on a player's overall score. For instance, if a player makes 1 3-pointer and turns the ball over once, the net difference would still be 3 points. Given this, I suspected that points and minutes would show the highest correlation with fantasy points scored. 

![Min to FP Correlation](https://github.com/jc98924/nba_dfs_projection/blob/master/img/minute_fp_correlation.png)

![Pts to FP Correlation](https://github.com/jc98924/nba_dfs_projection/blob/master/img/points_fp_correlation.png)

The graphs shown above corroborate this. Points scored (r = 0.92) and minutes played (r = 0.87) show the highest correlation with fantasy points scored.

https://github.com/jc98924/nba_dfs_projection/blob/master/data_collection.ipynb

### Feature Selection & Engineering

When formulating the problem, the first thing that I had to consider was what information that I would actually have access to as the season unfolds. Although I had every game log, I realistically could not use those statistics in my training set until after the game. Below are some of the features that I engineered.

* **Lagged Statistical Features**: for rolling 4, 8, 14, and season averages going **into each game**. 4, 8, and 14 games roughly simulate a week, two weeks, and a month. These time frames were added to capture the cold and hot streaks a player tends to go through over the course of a season.

* **Adjusted Usage Rate**: The term usage rate tends to be misleading if you actually take time to look at the calculation. From the formula listed below you can see that only attempted field goals, free throws, and turnovers are accounted for. This metric is more suited to capturing how effectively a playing uses his scoring opportunities. 

  ```
  100 * ((FGA + 0.44 * FTA + TOV) * (Team MP / 5)) / (MP * (Team FGA + 0.44 * Team FTA + Team TOV))
  ```

  I calculated my own metric that accounts for assists and also penalizes turnovers to match the DraftKings scoring system. 

  ```
  custom_usage = (100*((FGA) + (0.44 * FTA) + (0.5 * AST) - (0.3 * TOV)) * (df['Team MP']))/ (((Team FGA) + (0.44 * Team FTA) + (0.5 * Team AST) - (0.3 * Team TOV)) * 5 * (MP)
  ```

  **Team Level Aggregations**: I wanted to capture factors that could potentially cause a team to play certain players more or less.  This include: 

  * Days since last game
  * Average point differential 
  * Team Win%

### Model Results & Conclusion

After training the model on the train/validation set, the model that ended up producing the best results was the Lasso regression with degree 2 polynomial features. The r^2 for the test set was 0.01201 higher than FantasyCruncher's own projections and while that doesn't seem particularly significant at first glance, I'll definitely take this as a win given that these projection sites have their own teams of statisticians that do modeling work. Although my model marginally outperforms FantasyCruncher's in certain instances, it definitely could not do so on a consistent basis. My model's projections systematically under-predicts fantasy points while FantasyCruncher's over-predicts compared to the actual values. Both projection models are unable to capture 'superstar' fantasy performances and there's definitely a lot of money to be made if it can be modeled.  

As of now, this model performs well enough to be used as a tool in my analysis flow, although it is nowhere near comprehensive enough to use as my primary tool. For future work, there is definitely a lot of additional feature engineering that can be done and I look forward to refining my model going forward.  



