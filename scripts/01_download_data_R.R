# NHANES CHD Study - R-based Data Download
# Uses nhanesA package for reliable CDC data access

# Install required packages if needed
if (!require("nhanesA")) {
  install.packages("nhanesA", repos = "https://cloud.r-project.org")
}

library(nhanesA)

# Set output directory
output_dir <- "data/raw"

# Define cycles and files to download
cycles <- c(
  "1999-2000", "2001-2002", "2003-2004", "2005-2006",
  "2007-2008", "2009-2010", "2011-2012", "2013-2014", "2015-2016"
)

# File name mappings for each cycle
file_suffixes <- c(
  "1999-2000" = "",
  "2001-2002" = "_B",
  "2003-2004" = "_C",
  "2005-2006" = "_D",
  "2007-2008" = "_E",
  "2009-2010" = "_F",
  "2011-2012" = "_G",
  "2013-2014" = "_H",
  "2015-2016" = "_I"
)

# Components to download
components <- c("DEMO", "MCQ", "BPQ", "DIQ", "SMQ", "PAQ", "BMX", "BPX")

# Download each cycle
for (cycle in cycles) {
  cat("\n--- Processing", cycle, "---\n")
  suffix <- file_suffixes[cycle]
  cycle_year <- substr(cycle, 1, 4)
  
  cycle_dir <- file.path(output_dir, cycle)
  dir.create(cycle_dir, recursive = TRUE, showWarnings = FALSE)
  
  for (comp in components) {
    file_name <- paste0(comp, suffix)
    cat("  Downloading", file_name, "...")
    
    tryCatch({
      df <- nhanes(file_name)
      save_path <- file.path(cycle_dir, paste0(file_name, ".rds"))
      saveRDS(df, save_path)
      cat(" OK (", nrow(df), " rows)\n")
    }, error = function(e) {
      cat(" FAILED:", e$message, "\n")
    })
  }
}

cat("\n=== Download Complete ===\n")
cat("Files saved to:", output_dir, "\n")
