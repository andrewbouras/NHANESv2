# NHANES CHD Study - R Survey-Weighted Analysis (35-Year)
# Production-ready analysis with age standardization and proper trend testing
# Updated: December 2024

# =============================================================================
# Setup
# =============================================================================
library(survey)
library(arrow)

# Set options for survey package - certainty adjustment for lonely PSUs
options(survey.lonely.psu = "certainty")

cat("============================================================\n")
cat("NHANES CHD STUDY - SURVEY-WEIGHTED ANALYSIS\n")
cat("============================================================\n\n")

# =============================================================================
# Data Loading and Preparation
# =============================================================================
cat("[1/8] Loading data...\n")
data_path <- "data/processed/nhanes_chd_full_35year.parquet"
df <- read_parquet(data_path)
cat("  Loaded:", nrow(df), "participants from harmonized dataset\n")

# Filter to analysis population
df <- subset(df, RIDAGEYR >= 20 & !is.na(chd_composite) & WTMEC2YR > 0)
cat("  After exclusions:", nrow(df), "adults ≥20 with valid CHD and MEC weights\n\n")

# Ensure numeric types
df$chd_composite <- as.numeric(df$chd_composite)
df$WTMEC2YR <- as.numeric(df$WTMEC2YR)
df$SDMVSTRA <- as.numeric(df$SDMVSTRA)
df$SDMVPSU <- as.numeric(df$SDMVPSU)
df$RIAGENDR <- as.numeric(df$RIAGENDR)
df$RIDRETH1 <- as.numeric(df$RIDRETH1)

# =============================================================================
# Create Age Categories and Era Variables
# =============================================================================
cat("[2/8] Creating age categories and era variables...\n")

# Age categories matching 2000 US Standard Population
df$age_cat <- cut(df$RIDAGEYR, 
                  breaks = c(20, 30, 40, 50, 60, 70, 80, Inf), 
                  labels = c("20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"), 
                  right = FALSE)

# Create numeric era variable for trend testing
era_order <- c("Era1_1988-1994" = 1, "Era2_1999-2006" = 2, "Era3_2007-2014" = 3,
               "Era4a_2015-2020" = 4, "Era4b_2021-2023" = 5)
df$era_num <- era_order[df$era]

# Sex labels
df$sex_label <- factor(df$RIAGENDR, levels = c(1, 2), labels = c("Male", "Female"))

cat("  Age categories and era variables created\n\n")

# =============================================================================
# 2000 US Standard Population Weights for Direct Age Standardization
# =============================================================================
# From CDC/NCHS: https://www.cdc.gov/nchs/data/statnt/statnt20.pdf
std_pop_weights <- c(
  "20-29" = 0.1318,
  "30-39" = 0.1342,
  "40-49" = 0.1354,
  "50-59" = 0.0933,
  "60-69" = 0.0640,
  "70-79" = 0.0463,
  "80+"   = 0.0229
)
# Renormalize to sum to 1 for adults 20+
std_pop_weights <- std_pop_weights / sum(std_pop_weights)

# =============================================================================
# Survey Design Object
# =============================================================================
cat("[3/8] Creating survey design object...\n")
nhanes_design <- svydesign(
  id = ~SDMVPSU,
  strata = ~SDMVSTRA,
  weights = ~WTMEC2YR,
  nest = TRUE,
  data = df
)
cat("  Survey design created with Taylor series linearization\n\n")

# =============================================================================
# Table 1: Crude Survey-Weighted CHD Prevalence by Era
# =============================================================================
cat("[4/8] Computing crude survey-weighted CHD prevalence by era...\n")
cat("=== CRUDE SURVEY-WEIGHTED CHD PREVALENCE BY ERA ===\n\n")

crude_results <- data.frame()
eras <- c("Era1_1988-1994", "Era2_1999-2006", "Era3_2007-2014", 
          "Era4a_2015-2020", "Era4b_2021-2023")
era_labels <- c("1988-1994", "1999-2006", "2007-2014", 
                "2015-March 2020", "Aug 2021-Aug 2023")

for (i in seq_along(eras)) {
  era_val <- eras[i]
  era_subset <- subset(nhanes_design, era == era_val)
  n <- nrow(era_subset$variables)
  
  if (n > 0) {
    tryCatch({
      prev <- svymean(~chd_composite, design = era_subset, na.rm = TRUE)
      ci <- confint(prev)
      
      cat(sprintf("  %s: %.2f%% (95%% CI: %.2f%%-%.2f%%), n=%d\n",
                  era_labels[i],
                  coef(prev) * 100,
                  ci[1] * 100,
                  ci[2] * 100,
                  n))
      
      crude_results <- rbind(crude_results, data.frame(
        era = era_val,
        era_label = era_labels[i],
        n = n,
        prevalence = coef(prev) * 100,
        se = SE(prev) * 100,
        ci_low = ci[1] * 100,
        ci_high = ci[2] * 100
      ))
    }, error = function(e) {
      cat(sprintf("  %s: Error - %s\n", era_labels[i], e$message))
    })
  }
}

write.csv(crude_results, "output/tables/R_survey_prevalence_by_era.csv", row.names = FALSE)
cat("\n  Saved: output/tables/R_survey_prevalence_by_era.csv\n\n")

# =============================================================================
# Table 2: Direct Age-Standardized CHD Prevalence by Era
# =============================================================================
cat("[5/8] Computing age-standardized CHD prevalence by era...\n")
cat("=== AGE-STANDARDIZED CHD PREVALENCE BY ERA ===\n")
cat("    (Direct standardization to 2000 US Standard Population)\n\n")

age_std_results <- data.frame()

for (i in seq_along(eras)) {
  era_val <- eras[i]
  era_df <- subset(df, era == era_val)
  
  if (nrow(era_df) > 100) {
    era_design <- svydesign(
      id = ~SDMVPSU, strata = ~SDMVSTRA, weights = ~WTMEC2YR,
      nest = TRUE, data = era_df
    )
    
    tryCatch({
      # Get age-specific prevalences
      age_prev <- svyby(~chd_composite, ~age_cat, design = era_design, 
                        svymean, na.rm = TRUE)
      
      # Direct age standardization
      age_cats_present <- as.character(age_prev$age_cat)
      prev_vals <- age_prev$chd_composite
      se_vals <- SE(age_prev)
      
      # Compute age-standardized prevalence
      weights_present <- std_pop_weights[age_cats_present]
      weights_present <- weights_present / sum(weights_present)  # renormalize
      
      std_prev <- sum(prev_vals * weights_present)
      # Variance of weighted sum (assuming independence)
      std_var <- sum((weights_present^2) * (se_vals^2))
      std_se <- sqrt(std_var)
      
      ci_low <- std_prev - 1.96 * std_se
      ci_high <- std_prev + 1.96 * std_se
      
      cat(sprintf("  %s: %.2f%% (95%% CI: %.2f%%-%.2f%%)\n",
                  era_labels[i],
                  std_prev * 100,
                  ci_low * 100,
                  ci_high * 100))
      
      age_std_results <- rbind(age_std_results, data.frame(
        era = era_val,
        era_label = era_labels[i],
        n = nrow(era_df),
        prevalence_age_std = std_prev * 100,
        se = std_se * 100,
        ci_low = ci_low * 100,
        ci_high = ci_high * 100
      ))
      
    }, error = function(e) {
      cat(sprintf("  %s: Error - %s\n", era_labels[i], e$message))
    })
  }
}

write.csv(age_std_results, "output/tables/R_age_standardized_prevalence_by_era.csv", row.names = FALSE)
cat("\n  Saved: output/tables/R_age_standardized_prevalence_by_era.csv\n\n")

# =============================================================================
# Table 3: CHD Prevalence by Sex and Era (with CIs)
# =============================================================================
cat("[6/8] Computing CHD prevalence by sex and era...\n")
cat("=== CHD PREVALENCE BY SEX AND ERA ===\n\n")

sex_results <- data.frame()
for (i in seq_along(eras)) {
  era_val <- eras[i]
  for (sex_val in c("Male", "Female")) {
    era_sex_df <- subset(df, era == era_val & sex_label == sex_val)
    
    if (nrow(era_sex_df) > 50) {
      era_sex_design <- svydesign(
        id = ~SDMVPSU, strata = ~SDMVSTRA, weights = ~WTMEC2YR,
        nest = TRUE, data = era_sex_df
      )
      
      tryCatch({
        prev <- svymean(~chd_composite, design = era_sex_design, na.rm = TRUE)
        ci <- confint(prev)
        
        cat(sprintf("  %s - %s: %.2f%% (95%% CI: %.2f%%-%.2f%%)\n",
                    era_labels[i], sex_val, coef(prev) * 100, ci[1] * 100, ci[2] * 100))
        
        sex_results <- rbind(sex_results, data.frame(
          era = era_val,
          era_label = era_labels[i],
          sex = sex_val,
          n = nrow(era_sex_df),
          prevalence = coef(prev) * 100,
          se = SE(prev) * 100,
          ci_low = ci[1] * 100,
          ci_high = ci[2] * 100
        ))
      }, error = function(e) {})
    }
  }
}

write.csv(sex_results, "output/tables/R_survey_prevalence_by_sex.csv", row.names = FALSE)
cat("\n  Saved: output/tables/R_survey_prevalence_by_sex.csv\n\n")

# =============================================================================
# Table 4: CHD Prevalence by Race/Ethnicity and Era (with CIs)
# =============================================================================
cat("[7/8] Computing CHD prevalence by race/ethnicity and era...\n")
cat("=== CHD PREVALENCE BY RACE/ETHNICITY AND ERA ===\n\n")

# Race labels (RIDRETH1 coding)
race_labels <- c(
  "1" = "Mexican American",
  "2" = "Other Hispanic", 
  "3" = "Non-Hispanic White",
  "4" = "Non-Hispanic Black",
  "5" = "Other/Multi-racial"
)

race_results <- data.frame()
# Skip Era 1 (NHANES III has different race coding)
for (i in 2:length(eras)) {
  era_val <- eras[i]
  era_df <- subset(df, era == era_val)
  
  for (race_code in names(race_labels)) {
    era_race_df <- subset(era_df, RIDRETH1 == as.numeric(race_code))
    
    if (nrow(era_race_df) > 30) {
      era_race_design <- svydesign(
        id = ~SDMVPSU, strata = ~SDMVSTRA, weights = ~WTMEC2YR,
        nest = TRUE, data = era_race_df
      )
      
      tryCatch({
        prev <- svymean(~chd_composite, design = era_race_design, na.rm = TRUE)
        ci <- confint(prev)
        
        race_results <- rbind(race_results, data.frame(
          era = era_val,
          era_label = era_labels[i],
          race_ethnicity = race_labels[race_code],
          n = nrow(era_race_df),
          prevalence = coef(prev) * 100,
          se = SE(prev) * 100,
          ci_low = ci[1] * 100,
          ci_high = ci[2] * 100
        ))
      }, error = function(e) {})
    }
  }
}

write.csv(race_results, "output/tables/R_survey_prevalence_by_race.csv", row.names = FALSE)
cat("  Saved: output/tables/R_survey_prevalence_by_race.csv\n\n")

# =============================================================================
# Trend Testing
# =============================================================================
cat("[8/8] Running trend tests...\n")
cat("============================================================\n")
cat("TREND ANALYSIS\n")
cat("============================================================\n\n")

# --- Unadjusted Trend Model ---
cat("--- UNADJUSTED TREND MODEL ---\n")
cat("Model: logit(CHD) ~ era_num\n\n")

tryCatch({
  model_unadj <- svyglm(chd_composite ~ era_num, design = nhanes_design, 
                        family = quasibinomial())
  unadj_coef <- summary(model_unadj)$coefficients
  print(round(unadj_coef, 4))
  
  era_unadj <- unadj_coef["era_num", ]
  cat(sprintf("\nUnadjusted era coefficient: %.4f (SE: %.4f), p = %.4f\n",
              era_unadj[1], era_unadj[2], era_unadj[4]))
}, error = function(e) {
  cat("Unadjusted trend test error:", e$message, "\n")
})

cat("\n")

# --- Age-Adjusted Trend Model ---
cat("--- AGE-ADJUSTED TREND MODEL ---\n")
cat("Model: logit(CHD) ~ era_num + age_cat\n")
cat("       (age categories: 20-29, 30-39, 40-49, 50-59, 60-69, 70-79, 80+)\n\n")

tryCatch({
  model_adj <- svyglm(chd_composite ~ era_num + age_cat, design = nhanes_design, 
                      family = quasibinomial())
  adj_coef <- summary(model_adj)$coefficients
  print(round(adj_coef, 4))
  
  era_adj <- adj_coef["era_num", ]
  cat(sprintf("\nAge-adjusted era coefficient: %.4f (SE: %.4f), p = %.4f\n",
              era_adj[1], era_adj[2], era_adj[4]))
  
  # Save trend results
  trend_results <- data.frame(
    model = c("Unadjusted", "Age-adjusted"),
    era_coefficient = c(unadj_coef["era_num", 1], adj_coef["era_num", 1]),
    std_error = c(unadj_coef["era_num", 2], adj_coef["era_num", 2]),
    t_value = c(unadj_coef["era_num", 3], adj_coef["era_num", 3]),
    p_value = c(unadj_coef["era_num", 4], adj_coef["era_num", 4])
  )
  write.csv(trend_results, "output/tables/R_trend_test_results.csv", row.names = FALSE)
  cat("\n  Saved: output/tables/R_trend_test_results.csv\n")
  
}, error = function(e) {
  cat("Age-adjusted trend test error:", e$message, "\n")
})

# =============================================================================
# Summary Statistics
# =============================================================================
cat("\n============================================================\n")
cat("SUMMARY STATISTICS\n")
cat("============================================================\n\n")

# Overall prevalence
overall_prev <- svymean(~chd_composite, design = nhanes_design, na.rm = TRUE)
overall_ci <- confint(overall_prev)
cat(sprintf("Overall crude prevalence: %.2f%% (95%% CI: %.2f%%-%.2f%%)\n",
            coef(overall_prev) * 100, overall_ci[1] * 100, overall_ci[2] * 100))

# Sample sizes by era
cat("\nSample sizes by era:\n")
for (i in seq_along(eras)) {
  n_era <- sum(df$era == eras[i])
  cat(sprintf("  %s: n = %d\n", era_labels[i], n_era))
}
cat(sprintf("\n  Total: n = %d\n", nrow(df)))

cat("\n============================================================\n")
cat("ANALYSIS COMPLETE\n")
cat("============================================================\n")
cat("\nOutput files:\n")
cat("  - output/tables/R_survey_prevalence_by_era.csv (crude)\n")
cat("  - output/tables/R_age_standardized_prevalence_by_era.csv\n")
cat("  - output/tables/R_survey_prevalence_by_sex.csv\n")
cat("  - output/tables/R_survey_prevalence_by_race.csv\n")
cat("  - output/tables/R_trend_test_results.csv\n")
