# 🎨 sinicx-template

[![build](https://github.com/omron-sinicx/projectpage-template/actions/workflows/build.yaml/badge.svg)](https://github.com/omron-sinicx/projectpage-template/actions/workflows/build.yaml) [![build](https://github.com/omron-sinicx/projectpage-template/actions/workflows/lint.yaml/badge.svg)](https://github.com/omron-sinicx/projectpage-template/actions/workflows/lint.yaml)

- A project page template built with ⚛️ [React](https://ja.reactjs.org/) + 🎨 [UIKit](https://getuikit.com/)
- **Demo**: ⛅[light-theme](https://omron-sinicx.github.io/mabr/) / [src](https://github.com/omron-sinicx/mabr/tree/project-page) 🕶️ [dark-theme](https://omron-sinicx.github.io/maru/) / [src](https://github.com/omron-sinicx/mabr/tree/project-page)

> [!TIP]
> You can switch themes by setting [theme field in template.yaml](https://github.com/omron-sinicx/projectpage-template/blob/main/template.yaml#L1-L2)

```yaml
theme: default # default || dark
```

## 🚀 Getting Started

### 📋 Prerequisites | 🪟WSL 🐧Linux 🍎MacOS

#### 🔧 Pixi Installation

We use [Pixi](https://pixi.sh/) to manage the toolchain (e.g. `node.js`):

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

Restart your shell so `pixi` is on your `PATH`.

## 🛠️ Development

### 📥 Installation

```sh
pixi install
```

### 💻 Development Mode

```bash
pixi run dev
```

### 🏗️ Production Mode

```bash
pixi run preview
```

#### 🏗️ Static pre-rendering

`pixi run preview` builds the site with [`vite-react-ssg`](https://github.com/Daydreamer-riri/vite-react-ssg)
to pre-render the page to static HTML at build time (no headless browser /
Puppeteer required). This bakes the OGP/Twitter meta tags into `<head>` so
crawlers can read them without running JavaScript, and links the CSS in
`<head>` so there is no flash of unstyled content (FOUC). A successful build
ends with:

```sh
[vite-react-ssg] Rendering Pages... (1)
build/index.html
[vite-react-ssg] Build finished.
```

### 📋 Template

Complete `template.yaml` by filling in the required values. Use null for any unavailable content (e.g., `blog: null`).

```yaml
organization: OMRON SINIC X
twitter: "@omron_sinicx"
title: Path Planning using Neural A* Search
conference: ICML2021
resources:
  paper: https://arxiv.org/abs/1909.13111
  code: https://github.com/omron-sinicx/multipolar
  video: https://www.youtube.com/embed/adUnIj83RtU
  blog: https://medium.com/sinicx/multipolar-multi-source-policy-aggregation-for-transfer-reinforcement-learning-between-diverse-bc42a152b0f5
  ...
```

## 🎨 Customization

### 🔧 Styling

- Customize appearance by modifying UIKit variables in `src/scss/theme.scss` (zero hand-written CSS)
- Extend `*.jsx` files with components from:
  - 🎨 [UIKit Components](https://getuikit.com/docs/introduction)
  - 🎯 [React-Icons](https://react-icons.github.io/react-icons/)

### 📁 Project Structure

```
template.yaml       # Configuration
src/
├── components/     # React components
├── html/           # HTML templates
├── media/          # Media assets (relocated to assets/ automatically)
├── videos/         # Video content
├── js/             # JavaScript files
├── pages/          # Page templates
└── scss/           # Styling
```

## 🚀 Release your project page automatically by GitHub Actions

- example project: https://github.com/omron-sinicx/mabr/tree/project-page

### :octocat: Deploy from GitHub Actions

- Navigate to `https://github.com/{your-github-repo-path}/settings/pages`
- Select **GitHub Actions** at Build and Deployment > Source
- See also: [GitHub Documentation](https://docs.github.com/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) and [actions/deploy-pages](https://github.com/actions/deploy-pages)

![image](https://github.com/user-attachments/assets/4f1ad0f3-46f8-4ab0-8a0c-062d2fba7b46)

> [!NOTE]
> When using GitHub Actions to deploy a site on GitHub Pages, the source code is built internally during the workflow run. Only the build artifacts (e.g., HTML, CSS, JS) are deployed to the GitHub Pages environment, while the repository itself retains only the source code.

### 🌿 Push project page source to "project-page" branch

- `$ git remote add github {your-github-repo-path}`
- `$ git push github {local-project-page-branch}:project-page`
- See also: https://github.com/omron-sinicx/projectpage-template/blob/main/.github/workflows/deploy.yaml

### TroubleShooting

<details>
<summary>Branch "project-page" is not allowed to deploy to github-pages due to environment protection rules</summary>
Navigate to Settings > Environments > github-pages > 🗑️
  
![image](https://github.com/user-attachments/assets/ddaa751d-cedc-4665-86a1-8afd88e04e52)

</details>

## 🔍 SEO & Social Sharing

### 🌐 OGP Support

- OGP meta tags are [automatically generated](https://github.com/omron-sinicx/projectpage-template/blob/main/src/pages/index.jsx) from `template.yaml` and baked into the static HTML at build time by `vite-react-ssg`, so they render correctly both for local builds (`pixi run preview`) and when deployed via **GitHub Actions (see above)**.
- Example: [Twitter Card Preview](https://x.com/omron_sinicx/status/1847150071143715312)

## 🪝 Git Hooks & Typo Checking

### Automatic Formatting & Typo Checking

Git hooks are managed by [prek](https://github.com/j178/prek) (a fast `pre-commit` reimplementation, installed by pixi) and configured in `.pre-commit-config.yaml`. They run `prettier` and `typos` on staged files only. Install the hook once per clone:

```bash
pixi run hooks
```

### Manual Checking

```bash
pixi run hooks:all  # run every hook against all files
pixi run typos      # typo check only
pixi run typos:fix  # typo check and apply fixes
```

### Disabling Git Hooks

To skip all hooks for a single commit:

```bash
git commit --no-verify
```

To skip only some of them, list the hook ids from `.pre-commit-config.yaml`:

```bash
SKIP=typos,prettier git commit -m "wip"
```

Note that `.claude/` is excluded from every hook (see `exclude:` in `.pre-commit-config.yaml`).

## 🤝 Contributing

Issues and PRs welcome! Feel free to [open an issue](https://github.com/omron-sinicx/projectpage-template/issues)
