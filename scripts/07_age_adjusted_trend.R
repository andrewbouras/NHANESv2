# Age-Adjusted Trend Analysis for PI Report
# Run with: Rscript scripts/07_age_adjusted_trend.R

cat("[1/6] Loading packages...\n"); flush.console()
library(survey)
library(arrow)
options(survey.lonely.psu = "certainty")

cat("[2/6] Loading data...\n"); flush.console()
df <- read_parquet("data/processed/nhanes_chd_full_35year.parquet")
df <- subset(df, RIDAGEYR >= 20 & !is.na(chd_composite) & WTMEC2YR > 0)
cat("    Analytic sample:", nrow(df), "\n"); flush.console()

cat("[3/6] Creating variables...\n"); flush.console()
df$age_cat <- cut(df$RIDAGEYR, 
                  breaks = c(20, 30, 40, 50, 60, 70, 80, Inf), 
                  labels = c("20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"), 
                  right = FALSE)

era_order <- c("Era1_1988-1994" = 1, "Era2_1999-2006" = 2, "Era3_2007-2014" = 3, 
               "Era4a_2015-2020" = 4, "Era4b_2021-2023" = 5)
df$era_num <- era_order[df$era]

# Convert to numeric
df$chd_composite <- as.numeric(df$chd_composite)
df$WTMEC2YR <- as.numeric(df$WTMEC2YR)
df$SDMVSTRA <- as.numeric(df$SDMVSTRA)
df$SDMVPSU <- as.numeric(df$SDMVPSU)

cat("[4/6] Creating survey design...\n"); flush.console()
design <- svydesign(
  id = ~SDMVPSU, 
  strata = ~SDMVSTRA, 
  weights = ~WTMEC2YR,
  nest = TRUE, 
  data = df
)

cat("[5/6] Running age-adjusted trend model...\n"); flush.console()
model_adj <- svyglm(chd_composite ~ era_num + age_cat, 
                    design = design, 
                    family = quasibinomial())

cat("[6/6] Results:\n\n"); flush.console()

cat("============================================================\n")
cat("AGE-ADJUSTED TREND MODEL\n")
cat("Model: logit(CHD) ~ era_num + age_cat\n")
cat("============================================================\n\n")
print(round(summary(model_adj)$coefficients, 4))

# Extract key values for report
era_coef <- summary(model_adj)$coefficients["era_num", ]
cat("\n--- Key Result ---\n")
cat(sprintf("Era trend coefficient: %.4f (SE: %.4f)\n", era_coef[1], era_coef[2]))
cat(sprintf("t-value: %.3f, p-value: %.4f\n", era_coef[3], era_coef[4]))

cat("\n============================================================\n")
cat("UNADJUSTED TREND MODEL (for comparison)\n")
cat("============================================================\n\n")
model_unadj <- svyglm(chd_composite ~ era_num, design = design, family = quasibinomial())
print(round(summary(model_unadj)$coefficients, 4))

cat("\n============================================================\n")
cat("DONE\n")
cat("============================================================\n")
