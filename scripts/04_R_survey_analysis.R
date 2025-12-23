# NHANES CHD Study - R Survey-Weighted Analysis (35-Year)
# Uses proper complex survey design for publication-ready estimates

# Load packages
library(survey)
library(arrow)

# Set options for survey package
options(survey.lonely.psu = "certainty")

cat("============================================================\n")
cat("NHANES CHD STUDY - SURVEY-WEIGHTED ANALYSIS\n")
cat("============================================================\n\n")

# Load harmonized data
data_path <- "data/processed/nhanes_chd_full_35year.parquet"
df <- read_parquet(data_path)
cat("Loaded:", nrow(df), "participants\n")

# Filter to analysis population
df <- subset(df, RIDAGEYR >= 20 & !is.na(chd_composite) & WTMEC2YR > 0)
cat("After exclusions:", nrow(df), "adults\n\n")

# Ensure numeric types
df$chd_composite <- as.numeric(df$chd_composite)
df$WTMEC2YR <- as.numeric(df$WTMEC2YR)
df$SDMVSTRA <- as.numeric(df$SDMVSTRA)
df$SDMVPSU <- as.numeric(df$SDMVPSU)
df$RIAGENDR <- as.numeric(df$RIAGENDR)
df$RIDRETH1 <- as.numeric(df$RIDRETH1)

# Create survey design object
# NOTE: Combining multiple cycles requires careful weight adjustment
# For this analysis, we treat each era as separate analysis domain
nhanes_design <- svydesign(
  id = ~SDMVPSU,
  strata = ~SDMVSTRA,
  weights = ~WTMEC2YR,
  nest = TRUE,
  data = df
)

# =============================================================================
# Table 1: CHD Prevalence by Era (Survey-Weighted)
# =============================================================================
cat("=== CHD PREVALENCE BY ERA (SURVEY-WEIGHTED) ===\n\n")

results <- data.frame()
eras <- c("Era1_1988-1994", "Era2_1999-2006", "Era3_2007-2014", 
          "Era4a_2015-2020", "Era4b_2021-2023")

for (era_val in eras) {
  era_subset <- subset(nhanes_design, era == era_val)
  n <- nrow(era_subset$variables)
  
  if (n > 0) {
    tryCatch({
      prev <- svymean(~chd_composite, design = era_subset, na.rm = TRUE)
      ci <- confint(prev)
      
      cat(sprintf("%s: %.2f%% (95%% CI: %.2f%%-%.2f%%), n=%d\n",
                  era_val,
                  coef(prev) * 100,
                  ci[1] * 100,
                  ci[2] * 100,
                  n))
      
      results <- rbind(results, data.frame(
        era = era_val,
        n = n,
        prevalence = coef(prev) * 100,
        se = SE(prev) * 100,
        ci_low = ci[1] * 100,
        ci_high = ci[2] * 100
      ))
    }, error = function(e) {
      cat(sprintf("%s: Error - %s\n", era_val, e$message))
    })
  }
}

# Save results
write.csv(results, "output/tables/R_survey_prevalence_by_era.csv", row.names = FALSE)
cat("\nSaved: output/tables/R_survey_prevalence_by_era.csv\n")

# =============================================================================
# Table 2: CHD Prevalence by Sex and Era
# =============================================================================
cat("\n=== CHD PREVALENCE BY SEX AND ERA ===\n\n")

df$sex_label <- factor(df$RIAGENDR, levels = c(1, 2), labels = c("Male", "Female"))

sex_results <- data.frame()
for (era_val in eras) {
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
        
        cat(sprintf("%s - %s: %.2f%% (%.2f%%-%.2f%%)\n",
                    era_val, sex_val, coef(prev) * 100, ci[1] * 100, ci[2] * 100))
        
        sex_results <- rbind(sex_results, data.frame(
          era = era_val,
          sex = sex_val,
          n = nrow(era_sex_df),
          prevalence = coef(prev) * 100,
          ci_low = ci[1] * 100,
          ci_high = ci[2] * 100
        ))
      }, error = function(e) {})
    }
  }
}

write.csv(sex_results, "output/tables/R_survey_prevalence_by_sex.csv", row.names = FALSE)
cat("\nSaved: output/tables/R_survey_prevalence_by_sex.csv\n")

# =============================================================================
# Trend Test
# =============================================================================
cat("\n=== TREND TEST (LOGISTIC REGRESSION) ===\n\n")

# Create numeric era variable
era_order <- c("Era1_1988-1994" = 1, "Era2_1999-2006" = 2, "Era3_2007-2014" = 3,
               "Era4a_2015-2020" = 4, "Era4b_2021-2023" = 5)
df$era_num <- era_order[df$era]

# Update design
nhanes_design <- svydesign(
  id = ~SDMVPSU, strata = ~SDMVSTRA, weights = ~WTMEC2YR,
  nest = TRUE, data = df
)

# Logistic regression for trend
tryCatch({
  trend_model <- svyglm(chd_composite ~ era_num, design = nhanes_design, 
                        family = quasibinomial())
  cat("Trend coefficient (log odds per era):\n")
  print(summary(trend_model)$coefficients)
}, error = function(e) {
  cat("Trend test error:", e$message, "\n")
})

cat("\n============================================================\n")
cat("ANALYSIS COMPLETE\n")
cat("============================================================\n")
cat("\nOutput files:\n")
cat("  - output/tables/R_survey_prevalence_by_era.csv\n")
cat("  - output/tables/R_survey_prevalence_by_sex.csv\n")
