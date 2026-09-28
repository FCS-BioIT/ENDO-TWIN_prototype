#!/usr/bin/env Rscript
# Phase 2B C4 step 5: per-cell tables for the guarded value reader (values.py).
# Columns exactly donor_id, klf12_count, depth (no barcode), both from the canonical
# Cell Ranger 9.0.1 filtered_feature_bc_matrix (amendment 16), for the Step-4
# included cells only. KLF12 is selected by gene id. Prints only row counts; no value.
suppressPackageStartupMessages({
  library(Seurat)
  library(Matrix)
})
W <- "/scratch/dt_adoc_phase2b/candidate"
out <- file.path(W, "step5")
dir.create(out, showWarnings = FALSE)
man <- read.delim(file.path(W, "step4_cell_manifest.tsv"), stringsAsFactors = FALSE)
man <- man[man$included, ]
tables <- list()
for (lib in c("WSSS_END9397531", "WSSS_END9397535")) {
  base <- file.path(W, paste0("count_", lib), lib, "outs")
  m <- Read10X_h5(file.path(base, "filtered_feature_bc_matrix.h5"), use.names = FALSE)
  feats <- read.delim(gzfile(file.path(base, "filtered_feature_bc_matrix", "features.tsv.gz")),
                      header = FALSE, stringsAsFactors = FALSE)
  stopifnot(identical(feats[[1]], rownames(m)))
  row <- which(sub("\\.[0-9]+$", "", feats[[1]]) == "ENSG00000118922")
  stopifnot(length(row) == 1, feats[[2]][row] == "KLF12", feats[[3]][row] == "Gene Expression")
  keep <- man[man$library == lib, ]
  j <- match(keep$barcode, colnames(m))
  stopifnot(!anyNA(j))
  t <- data.frame(donor_id = keep$donor,
                  klf12_count = as.numeric(m[row, j]),
                  depth = as.numeric(Matrix::colSums(m[, j, drop = FALSE])))
  stopifnot(all(t$depth > 0), all(t$klf12_count <= t$depth))
  tables[[lib]] <- t
  write.table(t, file.path(out, paste0("per_cell_", lib, ".tsv")), sep = "\t",
              quote = FALSE, row.names = FALSE)
  cat(lib, "rows", nrow(t), "\n")
}
pooled <- do.call(rbind, tables)
write.table(pooled, file.path(out, "per_cell_pooled.tsv"), sep = "\t", quote = FALSE,
            row.names = FALSE)
cat("pooled rows", nrow(pooled), "\n")
