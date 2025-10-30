# Subshells: Bringing Multithreading to Jupyter Kernels

- JupyterCon 2025
- 2025-11-04

Deployed to github pages at https://ianthomas23.github.io/jupytercon2025-subshells/

## Build locally

You need to have `node.js` installed.

To build the HTML slides use

```bash
npm install
npm run html
```

which generates `output/index.html`

To generate a PDF file of the slides use

```bash
npm run pdf
```

which generates `subshells.pdf`.

## Serve demos locally

Create and activate a `micromamba` (or `pixi` or `conda` etc) environment and run `jupyter lab`:


```bash
micromamba create -f environment.yml
micromamba activate subshells
cd notebooks
jupyter lab
```
