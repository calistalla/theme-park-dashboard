# QueueWise — Theme Park Queue Operations

An operational review dashboard for the **PortAventura World attraction operations manager**.

**Team:** QueueWise — LI YIFEI, LI XIRUN, WANG XIBEI, SUN CHENGYU

## 1. Dataset and decision-maker

**Kaggle dataset:** [Disneyland Visitors Data (100+ Rides), uploaded by AyushTankha](https://www.kaggle.com/datasets/ayushtankha/hackathon).

The supplied files include attraction waiting times, operating schedules, attendance, weather and a data glossary. We use `waiting_times.csv` and the attraction-to-park mapping. One original waiting-time row describes one attraction during a 15-minute interval. `WAIT_TIME_MAX` is the maximum wait recorded within that interval, in minutes; it is not an individual visitor's waiting time.

### Provenance limitation

The dataset is suitable for this classroom dashboard because it provides structured, attraction-level records with timestamps, waiting times and operating-duration fields. Each row represents a 15-minute interval, supporting comparisons across attractions and recurring weekday-hour patterns. After cleaning and selecting the analysis window, the application uses a single 3.30 MB CSV, meeting the assignment’s file-size requirement. Zero opening-time records and invalid operating records are excluded, while valid zero waits are retained. The dashboard uses the supplied attraction labels to support operational prioritization; it does not establish the causes of long waits. 

### Analysis and deployment scope

The original waiting-time CSV has **3,509,324 rows and 14 columns**, approximately **383 MB**. We selected PortAventura World and cleaned its records in a Pandas notebook before exporting a smaller CSV:

| Processing stage | Rows |
| --- | ---: |
| Target park before cleaning | 2,369,821 |
| Excluded: zero opening time | 1,080,609 |
| Excluded: remaining invalid records | 3 |
| Retained target-park records | 1,289,209 |

Records with zero opening time were excluded from operating-period queue metrics. The remaining records were checked for missing values, nonnegative wait and operating durations, valid interval timestamps, and consistency between opening time, uptime and downtime. Valid zero waits and high waits were retained. No duplicate attraction–interval keys were found in the retained data.

For the app, we selected the final eight complete calendar weeks before the week containing the last observation: **20 June–14 August 2022**. This is a deterministic time-window subset, not a random sample or an aggregation. It supports a recent-period review and reduces deployment size while preserving exact medians and counts.

The exported `data/park_queue_snapshot.csv` contains **58,294 rows, 23 attractions and four columns**, occupying **3.30 MB**. Its columns are `date`, `interval_start`, `attraction` and `wait_minutes`. Actual retained records run from **21 June–14 August 2022**, on 55 dates. There are no retained records for 20 June; that date is not filled with zero. Three of the 26 mapped target-park attractions have no retained records in this window, which is not evidence that they permanently closed.

## 2. Why a dashboard?

### Who uses it and how often?

One attraction operations manager reviews it weekly before assigning operational checks and reviewing upcoming operating arrangements. In production, the manager would normally examine a rolling four-to-eight-week window. The application does not automatically advance its historical dates or refresh its snapshot.

### What decision does it support?

**If the operations manager sees a high proportion of operating records above 60 minutes for an attraction, they will prioritize an operational review; the weekday-hour heatmap helps them choose when to observe the attraction and examine operating logs.**

The review may lead to changes in operating capacity, staffing coverage, maintenance timing or visitor guidance, depending on the cause found. Waiting-time data alone does not establish that understaffing caused the problem or determine the optimal number of employees.

### What would happen without it?

For this proposed business scenario, the manager would inspect separate attraction logs and combine them with staff feedback. Repeated manual comparisons take time and can overemphasize memorable incidents while missing persistent patterns. We have not interviewed park management or measured that workload; no specific time or monetary savings are claimed.

### Why not just an email, report or alert?

The same manager repeatedly needs the same comparisons but may need to change dates and inspect a different attraction. A dashboard supports those follow-up questions in one place. A weekly email could summarize results but would not support this exploration. An alert is suitable for a sudden operational incident; it does not replace the recurring pattern review supported here.

## 3. EDA and dashboard choices

The notebook uses Pandas and Matplotlib to inspect shape, types, missing values, interval consistency, wait distributions, date coverage, facility differences and weekday-hour patterns.

Across the retained target-park history, the interval maximum wait has a median of **15 minutes**, a mean of approximately **23.02 minutes** and a 95th percentile of **65 minutes**. The proportions above 30, 45, 60 and 90 minutes are **25.20%, 12.40%, 5.68% and 0.95%** respectively. This supports showing typical conditions separately from the high-wait tail.

In the app's complete default snapshot, the median is **20 minutes** and **5.29%** of operating records exceed 60 minutes. Facility detail reveals concentration hidden by the park aggregate: Spiral Slide exceeds 60 minutes in **85.94%** of its records, compared with **43.49%** for Free Fall. These are descriptive findings, not causal estimates.

### Two headline metrics

| Metric | Definition | Why it matters |
| --- | --- | --- |
| Median interval maximum wait | Median of all retained interval maximum waits in the selected period | Describes typical recorded queue pressure without being dominated by a few extreme values |
| Operating records above 60 minutes | Count with `wait_minutes > 60`, divided by all retained records in the selected period | Describes the frequency of high recorded waits that the manager should investigate |

The denominator is records, not visitors or actual minutes spent queuing. The park aggregate weights attractions according to their retained record counts. A low park-wide percentage can coexist with a severe problem at one attraction.

### Two supporting charts and useful filters

1. **Top-five facility ranking:** shows the largest shares above 60 minutes among attractions with at least 14 observed dates in the selected period. Five facilities keep the first review focused; this is a priority shortlist, not a complete audit of every facility.
2. **Selected-attraction weekday-hour heatmap:** shows where high-wait records recur. A cell is gray if it has no data, fewer than four observed dates, or fewer than 16 records. The chart shows only the attraction's observed hour range, retaining missing cells inside it. Gray does not mean low wait.

The **date filter** changes both KPIs and both charts. The **attraction selector** changes only the detail heatmap, leaving the park overview unchanged. No park selector is needed because the user manages one park. Short selected periods can produce insufficient-coverage messages; those rules are deliberate safeguards, not evidence of good performance.

### What we chose not to show

- **The wait-time histogram:** useful in EDA for selecting the median and inspecting the tail, but less useful than a facility ranking for deciding what to inspect each week.
- **The all-history facility ranking and year-by-year totals:** useful for detecting coverage differences, but they mix different seasons, operating periods and attraction availability. The app instead compares facilities within the same selected recent-period window.

Weather, revenue and detailed capacity analyses are outside this compact dashboard's scope. We do not add charts or a predictive model merely because those options are available.

### Page order and potential misinterpretations

Top to bottom: team title and purpose; snapshot and selected-period captions; two park KPIs; facility ranking; facility selector and heatmap; collapsed definitions. This follows the manager's review sequence: assess the overview, choose a facility, then choose when to inspect. Raw transaction tables are omitted because they do not assist this weekly prioritization task. This is the final layout rationale; we do not claim that a paper sketch was completed before implementation.

The app explains the interval-maximum definition, the assumed 60-minute threshold, missing dates, coverage rules and uncertain provenance. Full-history coverage differs by year, and the eight-week snapshot represents one season rather than a typical year. Comparisons within the same selected period still reflect different observed hours and dates. The dashboard cannot establish causality or demonstrate that an intervention reduced waits.

## 4. Refresh, review and action

**Production refresh:** nightly, after a day's records are complete. Daily data keeps the review current and enables later inspection of a particular date. Minute-by-minute refresh would not change this tool's weekly planning decision and would add processing and monitoring overhead. This classroom app has no live feed or scheduled refresh.

**Management review:** weekly, using a rolling 28-to-56-day window so recurring weekdays can be assessed. Refresh and review are different schedules. Immediate breakdowns should be handled through a separate operational alert and response process.

**Metric to track:** the attraction-specific proportion of valid operating records exceeding 60 minutes, reviewed each week over the latest 28 days.

**Proposed action trigger:** if that proportion is at least **20%**, with at least **14 observed dates**, the manager contacts the attraction supervisor and reviews operating capacity, downtime and queue-management practices before the next planning meeting. One in five recorded intervals having a maximum above one hour is an interpretable screening threshold. Both the 60-minute wait threshold and the 20% frequency trigger are classroom business assumptions, not official standards or validated optimal cutoffs. They require calibration with actual managers. The prototype supports manual review through filtering and ranking; it does not send alerts, retain a weekly monitoring history or automatically flag this trigger.

**Stale-data cost:** a one-day delay is usually tolerable for a weekly review but can hide a newly emerging pattern. A week of stale data can leave the manager prioritizing last week's problems and delay corrective investigation. There are no cost or staffing records here, so the financial loss cannot be quantified.