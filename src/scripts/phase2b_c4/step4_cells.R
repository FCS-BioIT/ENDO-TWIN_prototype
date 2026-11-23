#!/usr/bin/env Rscript
# Phase 2B C4 step 4 (value-blind): QC, doublets, depositor donor and population join.
# Writes a cell MANIFEST only -- library, barcode, QC/doublet flags, donor, Celltype,
# included -- and per-donor counts. Reads no gene's value except the aggregate QC
# metrics (nCount_RNA, nFeature_RNA, mitoRatio); KLF12 is never touched.
#
# Frozen rules (preregistration; amendments 16/18):
#   layer      Cell Ranger 9.0.1 filtered UMI counts (filtered_feature_bc_matrix.h5)
#   QC         ADOC qc.R/utils_qc.R: finite mitoRatio (^MT-, percent), nFeature_RNA >= 500,
#              mitoRatio < 15, nCount_RNA >= 1000; then scDblFinder (1.20.2), doublets
#              removed; set.seed(47) once, libraries in order (ADOC's atlas label
#              transfer, which filters nothing, is not run)
#   donors     depositor 'demultiplexed' labels B44/U1/U2; any other label is dropped
#   population author Celltype, every value except 'Low QC'; the frozen list below;
#              any other label is a deviation and is excluded
#   join       our barcode without '-1' == depositor cell name without 'WSSS_END<lib>_'
suppressPackageStartupMessages({
  library(Seurat)
  library(scDblFinder)
  library(jsonlite)
})
W <- "/scratch/dt_adoc_phase2b/candidate"
libs <- c("WSSS_END9397531", "WSSS_END9397535")
donors <- c("B44", "U1", "U2")
epithelial <- c(
  "Ciliated", "Estrogen_induced_PGR+", "Inflamatory", "NH_d2_WNTi", "NH_d2_d6",
  "NH_d6", "NH_d6_WNTi", "Pre-ciliated", "Secretory_Ctrl", "Secretory_NOTCHi",
  "Secretory_WNTi"
)
set.seed(47)
manifest <- list()
summary <- list()
for (lib in libs) {
  counts <- Read10X_h5(file.path(W, paste0("count_", lib), lib, "outs",
                                 "filtered_feature_bc_matrix.h5"))
  sc <- CreateSeuratObject(counts = counts, project = lib)
  sc[["mitoRatio"]] <- PercentageFeatureSet(sc, pattern = "^MT-")
  all_bc <- colnames(sc)
  finite <- is.finite(sc$mitoRatio)
  sc <- sc[, which(finite)]
  sc <- subset(sc, subset = nFeature_RNA >= 500 & mitoRatio < 15 & nCount_RNA >= 1000)
  qc_bc <- colnames(sc)
  sce <- scDblFinder(as.SingleCellExperiment(sc), verbose = FALSE)
  singlet_bc <- colnames(sce)[sce$scDblFinder.class != "doublet"]

  dep <- read.delim(file.path(W, paste0(lib, "_cells.tsv")), check.names = FALSE,
                    stringsAsFactors = FALSE)
  names(dep)[1] <- "cell"
  dep$barcode <- paste0(sub(paste0("^", lib, "_"), "", dep$cell), "-1")
  m <- data.frame(library = lib, barcode = all_bc, stringsAsFactors = FALSE)
  m$qc_pass <- m$barcode %in% qc_bc
  m$singlet <- m$barcode %in% singlet_bc
  i <- match(m$barcode, dep$barcode)
  m$donor <- dep$demultiplexed[i]
  m$celltype <- dep$Celltype[i]
  m$included <- m$qc_pass & m$singlet & !is.na(i) & m$donor %in% donors &
    m$celltype %in% epithelial
  manifest[[lib]] <- m
  summary[[lib]] <- list(
    cellranger_cells = length(all_bc),
    nonfinite_mito = sum(!finite),
    qc_pass = length(qc_bc),
    singlets_after_scdblfinder = length(singlet_bc),
    depositor_cells = nrow(dep),
    depositor_cells_matched = sum(dep$barcode %in% all_bc),
    depositor_donor_labels = as.list(table(dep$demultiplexed, useNA = "ifany")),
    depositor_celltypes_found = sort(unique(dep$Celltype)),
    celltypes_outside_frozen_list = setdiff(sort(unique(dep$Celltype)), c(epithelial, "Low QC")),
    included = sum(m$included),
    included_by_donor = as.list(table(factor(m$donor[m$included], levels = donors)))
  )
}
man <- do.call(rbind, manifest)
write.table(man, file.path(W, "step4_cell_manifest.tsv"), sep = "\t", quote = FALSE,
            row.names = FALSE)
tot <- table(factor(man$donor[man$included], levels = donors))
summary$pooled_included_by_donor <- as.list(tot)
summary$donors_with_cells <- sum(tot > 0)
summary$min_reference_donors_met <- sum(tot > 0) >= 3
summary$versions <- list(R = R.version.string, Seurat = as.character(packageVersion("Seurat")),
                         SeuratObject = as.character(packageVersion("SeuratObject")),
                         scDblFinder = as.character(packageVersion("scDblFinder")))
writeLines(toJSON(summary, auto_unbox = TRUE, pretty = TRUE), file.path(W, "step4_summary.json"))
cat(readLines(file.path(W, "step4_summary.json")), sep = "\n")
