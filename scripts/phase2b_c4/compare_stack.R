#!/usr/bin/env Rscript
# Phase 2B C4 step 2: stack identification, WHOLE-MATRIX comparison only.
#
# Value-blind by construction: prints booleans, counts and one whole-matrix
# maximum; never a feature name, a per-feature value or the location of any
# difference. No row is subset or extracted by gene.
#
# Frozen criteria (preregistration.json comparability.stack_identification, as
# adjusted by amendment 13):
#   features  make.unique(gene_name) in order == deposited names; ids one-to-one
#             with gencode.v47.annotation.gtf genes; type "Gene Expression"
#   raw/filt  same barcodes, same non-zero feature-barcode-count triples
#   decontX   same barcodes, max |ours - deposited| <= 1e-6
suppressPackageStartupMessages({
  library(Matrix)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
mode <- args[1]
out_json <- args[length(args)]

read_lines <- function(p) {
  con <- if (grepl("\\.gz$", p)) gzfile(p) else file(p)
  on.exit(close(con))
  readLines(con)
}

triples_equal <- function(ours, ours_bc, dep, dep_bc) {
  res <- list(
    dims_ours = dim(ours), dims_deposit = dim(dep),
    barcodes_identical_in_order = identical(ours_bc, dep_bc),
    barcodes_set_equal = setequal(ours_bc, dep_bc) && !anyDuplicated(ours_bc) &&
      !anyDuplicated(dep_bc)
  )
  if (!res$barcodes_set_equal || nrow(ours) != nrow(dep)) {
    res$triples_identical <- FALSE
    return(res)
  }
  dep <- dep[, match(ours_bc, dep_bc), drop = FALSE]
  a <- summary(as(drop0(ours), "TsparseMatrix"))
  b <- summary(as(drop0(dep), "TsparseMatrix"))
  a <- a[order(a$j, a$i), ]
  b <- b[order(b$j, b$i), ]
  res$nnz_ours <- nrow(a)
  res$nnz_deposit <- nrow(b)
  res$triples_identical <- nrow(a) == nrow(b) && all(a$i == b$i) &&
    all(a$j == b$j) && all(a$x == b$x)
  if (!res$triples_identical && nrow(a) == nrow(b) &&
      all(a$i == b$i) && all(a$j == b$j)) {
    res$n_count_mismatches <- sum(a$x != b$x)
  }
  res
}

if (mode == "features") {
  # features OURS_features.tsv.gz GTF_GENES_TSV DEPOSIT_FEATURES OUT_NAMES OUT_JSON
  f <- read.delim(args[2], header = FALSE, stringsAsFactors = FALSE, quote = "")
  gtf <- read.delim(args[3], header = FALSE, stringsAsFactors = FALSE, quote = "")
  dep <- read_lines(args[4])
  names_ours <- make.unique(f[[2]])
  writeLines(names_ours, args[5])
  res <- list(
    n_ours = nrow(f), n_deposit = length(dep), n_gtf = nrow(gtf),
    names_in_order_equal_deposit = identical(names_ours, dep),
    ids_one_to_one_with_gtf_in_order =
      nrow(f) == nrow(gtf) && identical(sub("\\.[0-9]+(_PAR_Y)?$", "", f[[1]]), gtf[[1]]),
    ids_unique = !anyDuplicated(f[[1]]),
    all_type_gene_expression = all(f[[3]] == "Gene Expression")
  )
  res$pass <- res$names_in_order_equal_deposit && res$ids_one_to_one_with_gtf_in_order &&
    res$ids_unique && res$all_type_gene_expression
} else if (mode == "counts") {
  # counts OURS_MATRIX_DIR DEPOSIT_MTX DEPOSIT_BARCODES OUT_JSON
  ours <- readMM(file.path(args[2], "matrix.mtx.gz"))
  ours_bc <- read_lines(file.path(args[2], "barcodes.tsv.gz"))
  dep <- readMM(args[3])
  dep_bc <- read_lines(args[4])
  res <- triples_equal(ours, ours_bc, dep, dep_bc)
  res$pass <- isTRUE(res$triples_identical)
} else if (mode == "decontx") {
  # decontx OURS_DECONTX_H5 DEPOSIT_MTX DEPOSIT_BARCODES OUT_JSON
  suppressPackageStartupMessages(library(DropletUtils))
  sce <- read10xCounts(args[2], col.names = TRUE)
  ours <- as(counts(sce), "CsparseMatrix")
  ours_bc <- colnames(sce)
  dep <- readMM(args[3])
  dep_bc <- read_lines(args[4])
  res <- list(
    dims_ours = dim(ours), dims_deposit = dim(dep),
    barcodes_identical_in_order = identical(ours_bc, dep_bc),
    barcodes_set_equal = setequal(ours_bc, dep_bc)
  )
  if (res$barcodes_set_equal && nrow(ours) == nrow(dep)) {
    dep <- as(dep[, match(ours_bc, dep_bc), drop = FALSE], "CsparseMatrix")
    d <- ours - dep
    res$max_abs_entrywise_difference <- if (length(d@x)) max(abs(d@x)) else 0
    res$pass <- res$max_abs_entrywise_difference <= 1e-6
  } else {
    res$pass <- FALSE
  }
} else {
  stop("unknown mode ", mode)
}

writeLines(toJSON(res, auto_unbox = TRUE, pretty = TRUE, digits = NA), out_json)
cat(readLines(out_json), sep = "\n")
