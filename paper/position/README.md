# ICML 2026 Position Paper - Compilation Instructions

## Files

- `paper.tex` - Main LaTeX document
- `references.bib` - BibTeX references
- `icml2026.sty` - ICML 2026 style file
- `fancyhdr.sty` - Required dependency
- `algorithm.sty` - Required dependency
- `../figures/` - Figures directory (01.png, 03.png, 05.png used)

## Compilation

### Option 1: Local LaTeX (recommended)

Install a LaTeX distribution:
- **macOS**: `brew install --cask mactex` or MacTeX from https://www.tug.org/mactex/
- **Ubuntu/Debian**: `sudo apt install texlive-full`
- **Windows**: MiKTeX from https://miktex.org/

Then compile:

```bash
cd paper/position
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

### Option 2: Overleaf

1. Create a new project on https://overleaf.com
2. Upload all files: `paper.tex`, `references.bib`, `icml2026.sty`, `fancyhdr.sty`, `algorithm.sty`
3. Create a `figures/` folder and upload `01.png`, `03.png`, `05.png` from `../figures/`
4. Compile

## Page Count

The main body (Sections 1-6) should fit within **8 pages** for ICML submission.
References and Appendices (A, B, C) can extend beyond the 8-page limit.

## Important Notes

1. **Double-blind**: Remove author names before submission
2. **Figures**: Ensure `../figures/` path works or move figures to same directory
3. **References**: Run BibTeX to generate bibliography

## Submission Checklist

- [ ] Main body ≤ 8 pages
- [ ] Single PDF file
- [ ] File size ≤ 50MB
- [ ] Anonymous (no author info)
- [ ] Title starts with "Position:"
- [ ] Alternative Views section included in main body
