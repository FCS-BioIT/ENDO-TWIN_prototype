#!/usr/bin/env Rscript
# Value-blind reproducibility check of the pinned decontX stage: run 1 vs run 2.
# Prints only barcode identity/order, dimensions, nnz, the whole-matrix maximum
# absolute entrywise difference and a deterministic content hash of each matrix
# (its column pointers, row indices and values). No feature name, per-feature
# value or location of a difference is computed for output.
suppressPackageStartupMessages({
  library(Matrix)
  library(DropletUtils)
  library(jsonlite)
  library(digest)
})
args <- commandArgs(trailingOnly = TRUE)
load_run <- function(path) {
  sce <- read10xCounts(path, col.names = TRUE)
  list(x = as(counts(sce), "CsparseMatrix"), bc = colnames(sce))
}
content_hash <- function(m) {
  m <- drop0(m)
  digest(list(dim = dim(m), p = m@p, i = m@i, x = m@x), algo = "sha256")
}
a <- load_run(args[1])
b <- load_run(args[2])
res <- list(
  dims_run1 = dim(a$x), dims_run2 = dim(b$x),
  nnz_run1 = length(drop0(a$x)@x), nnz_run2 = length(drop0(b$x)@x),
  barcodes_identical_in_order = identical(a$bc, b$bc),
  content_sha256_run1 = content_hash(a$x),
  content_sha256_run2 = content_hash(b$x)
)
if (identical(dim(a$x), dim(b$x)) && res$barcodes_identical_in_order) {
  d <- a$x - b$x
  res$max_abs_entrywise_difference <- if (length(d@x)) max(abs(d@x)) else 0
  res$within_frozen_1e6 <- res$max_abs_entrywise_difference <= 1e-6
}
res$content_identical <- identical(res$content_sha256_run1, res$content_sha256_run2)
writeLines(toJSON(res, auto_unbox = TRUE, pretty = TRUE, digits = NA), args[3])
cat(readLines(args[3]), sep = "\n")
