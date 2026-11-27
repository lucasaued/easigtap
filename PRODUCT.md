# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Health professionals at the Hospital Universitário de Santa Maria (HUSM/UFSM) who need to consult SIGTAP procedures, diagnoses (CIDs), and compatible orthoses, prostheses, and special materials (OPM).

## Product Purpose

eaSIGTAP is a local evaluation prototype that makes SIGTAP data easier to consult. It brings together procedure and CID search, their recorded associations, official procedure–OPM compatibility, and a summary that the user can copy. The initial focus is Traumatology and Orthopedics.

## Positioning

The prototype combines procedure–CID associations from the project spreadsheet with procedure–OPM compatibility and CID descriptions from the official SIGTAP package for June 2026. It keeps those sources and their different meanings visible in the consultation flow.

## Operating Context

The user can search procedures by name or code, search CIDs by code or description, inspect a procedure and its related CIDs, select a CID, review officially compatible OPM for the procedure, select items, and copy a summary. The default `0408` code prefix is an initial navigation scope; users can search all procedures. Search results are limited to 60 per query, so broad searches need refinement.

## Capabilities and Constraints

- The current prototype runs locally and uses a PostgreSQL database populated from the supplied spreadsheet and the official SIGTAP June 2026 package.
- The `0408` scope has not been clinically confirmed as the definitive Traumatology and Orthopedics selection.
- Procedure–CID associations come from the supplied spreadsheet. Selecting a CID does not change which OPM are compatible with the procedure.
- Procedure–OPM compatibility comes from the official SIGTAP package for the procedure and competence. The displayed permitted quantity comes from that relationship, not the spreadsheet item's `Qtd Máxima` field.
- Compatibility and an empty result are not clinical suitability, registration guidance, or proof of prohibition. Additional registration conditions, specialty classification, and clinical adequacy await review with the team.
- The spreadsheet's June 2026 competence was supplied by the project responsible party. A technically validated import status is not a claim of full clinical or official verification.

## Brand Commitments

The product name is eaSIGTAP. The interface and project documentation use Brazilian Portuguese. The prototype identifies its local HUSM/UFSM evaluation context.

## Evidence on Hand

- `data/raw/Sigtap - UGPIA.xlsx`: supplied workbook, 4,984 records in the documented source tab.
- `data/raw/TabelaUnificada_202606_v2610231231.zip`: official SIGTAP package for June 2026, used for CID descriptions and procedure–OPM relationships.
- `docs/planilha-mvp.md`, `docs/data-quality.md`, and `docs/operacao.md`: source scope, data quality, and operating limits.
- `web/`: current local prototype interface.
- No clinical review of the final specialty scope, registration conditions, or suitability is documented.

## Product Principles

1. Make procedure, CID, and OPM relationships easy to find and inspect in one consultation flow.
2. Keep each source and the meaning of its relationships clear.
3. Treat the `0408` scope as a starting point while preserving access to the broader data.
4. Communicate data and clinical review limits wherever they affect interpretation.
