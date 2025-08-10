# sinicx-template
[![build](https://github.com/omron-sinicx/projectpage-template/actions/workflows/build.yaml/badge.svg)](https://github.com/omron-sinicx/projectpage-template/actions/workflows/build.yaml) [![build](https://github.com/omron-sinicx/projectpage-template/actions/workflows/lint.yaml/badge.svg)](https://github.com/omron-sinicx/projectpage-template/actions/workflows/lint.yaml)
- A project page template using [React](https://ja.reactjs.org/) + [UIKit](https://getuikit.com/)
- **Demo**: ⛅[light-theme](https://omron-sinicx.github.io/mabr/) 🕶️ dark-theme

> [!TIP]
> You can switch themes by setting [theme field in template.yaml](https://github.com/omron-sinicx/projectpage-template/blob/main/template.yaml#L1-L2)

```yaml
theme: default # default || dark
```

## Prerequisites
- Before you begin, ensure you have met the following requirements:
### 🪟WSL 🐧Linux 🍎MacOS
#### Install nodejs>=20 using [node version manager](https://volta.sh/)
```bash
$ curl https://get.volta.sh/ | bash
# restart your shell...
$ volta install node@20.11.0
$ volta pin node@20.11.0

$ node --version
v20.11.0
$ npm --version
10.2.4
```
#### Install puppeteer dependencies
- react-snap uses Headless Chromium through puppeteer to [pre-render React apps](https://blog.logrocket.com/pre-rendering-react-app-react-snap/).

```bash
sudo apt install -y libgtk2.0-0 libgtk-3-0 libnotify-dev libgconf-2-4 libnss3 libxss1 libasound2 libxtst6 xauth xvfb libgbm-dev fonts-ipafont
```

## Usage
### Installation
- Clone this repository

```sh
$ npm install
```
### Build
```sh
$ npm run clean
$ npm run build
$ npm run serve
```

### Develop
```sh
$ npm run serve
```

### Customize
- You can change styles without writing css. Modify [UIKit variables](https://github.com/uikit/uikit/blob/bc6dd1851652e5b77387a1efefc16cea6e3d165b/src/scss/variables.scss) at `src/scss/theme.scss`
- You can extend `*.jsx` files using these assets or custom React Components.
  - UIKit Components https://getuikit.com/docs/introduction
  - React-Icons https://react-icons.github.io/react-icons/

### Structure
```
template.yaml    # template arguments
src/
├── components          # React components loaded in index.jsx
│   ├── authors.jsx
│   ├── citation.jsx
│   ├── contact.jsx
│   ├── footer.jsx
│   ├── header.jsx
│   ├── method.jsx
│   ├── overview.jsx
│   ├── results.jsx
│   └── video.jsx
├── html
│   └── index.html
├── media # media files to be relocated to assets/ by file-loader
│   ├── method.png
│   ├── demo.mp4
│   └── teaser.png
├── videos
│   └── result1.mp4
├── js
│   └── styles.js        # embed styles to js
├── pages
│   └── index.jsx        # template root
└── scss                 # color theme zoo
    ├── dark-theme.scss
    └── theme.scss
```

### Template
- fillin values at `template.yaml`
- fillin `null` for N/A contents (e.g. `method: null`)

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
description: a Japanese stop-motion short anime series produced by Shin-Ei Animation and Japan Green Hearts in cooperation with Bandai Namco Entertainment.
image: https://omron-sinicx.github.io/neural-astar/assets/teaser.png
url: https://omron-sinicx.github.io/neural-astar
speakerdeck: b7a0614c24014dcbbb121fbb9ed234cd   # speakerdeck embed id
authors:
  - name: Ryo Yonetani*
    affiliation: [1]
    position: principal investigator
    url: https://yonetaniryo.github.io/
  - name: Tatsunori Taniai*
    affiliation: [1]
    position: senior researcher
  - name: Mohammadamin Barekatain
    affiliation: [1, 2]
    url: http://barekatain.me/
  - name: Mai Nishimura
    affiliation: [1]
    url: https://denkiwakame.github.io
  - name: Asako Kanezaki
    affiliation: [2]
    url: https://kanezaki.github.io/
contact_ids: [1]   # 0=1st author 1=2nd author
affiliations:
  - OMRON SINIC X
  - Technical University of Munich
  - Tokyo Institute of Technology
meta:
  - "* work done as an intern at OMRON SINIC X."
bibtex: >
  @article{DBLP:journals/corr/abs-2009-07476,
    author    = {Ryo Yonetani and
                 Tatsunori Taniai and
                 Mohammadamin Barekatain and
                 Mai Nishimura and
                 Asako Kanezaki},
    title     = {Path Planning using Neural A* Search},
    journal   = {CoRR},
    volume    = {abs/2009.07476},
    year      = {2020},
    url       = {https://arxiv.org/abs/2009.07476},
    archivePrefix = {arXiv},
    eprint    = {2009.07476},
    timestamp = {Wed, 23 Sep 2020 15:51:46 +0200},
    biburl    = {https://dblp.org/rec/journals/corr/abs-2009-07476.bib},
    bibsource = {dblp computer science bibliography, https://dblp.org}
  }
```

## Release your project page automatically by GitHub Actions
- example project: https://github.com/omron-sinicx/mabr/tree/project-page
### Deploy from GitHub Actions
- Navigate to `https://github.com/{your-github-repo-path}/settings/pages`
- Select **GitHub Actions** at Build and Deployment > Source
- See also: [GitHub Documentation](https://docs.github.com/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) and [actions/deploy-pages](https://github.com/actions/deploy-pages)

![image](https://github.com/user-attachments/assets/4f1ad0f3-46f8-4ab0-8a0c-062d2fba7b46)

> [!NOTE]
> When using GitHub Actions to deploy a site on GitHub Pages, the source code is built internally during the workflow run. Only the build artifacts (e.g., HTML, CSS, JS) are deployed to the GitHub Pages environment, while the repository itself retains only the source code.

### Push project page source to "project-page" branch
- `$ git remote add github {your-github-repo-path}`
- `$ git push github {local-project-page-branch}:project-page`
- See also: https://github.com/omron-sinicx/projectpage-template/blob/main/.github/workflows/deploy.yaml

### TroubleShooting

<details>
<summary>Branch "project-page" is not allowed to deploy to github-pages due to environment protection rules</summary>
Navigate to Settings > Environments > github-pages > 🗑️

![image](https://github.com/user-attachments/assets/ddaa751d-cedc-4665-86a1-8afd88e04e52)

</details>

## OGP (Open Graph Protocol)
- OGP meta tags are [automatically generated](https://github.com/omron-sinicx/projectpage-template/blob/main/src/pages/index.jsx#L20-L55) from `template.yaml` and correctly rendered when deployed via **GitHub Actions (see above)**.

> [!CAUTION]
>  For local builds, react-snap must work properly to convert output into static HTML. We recommend building via GitHub Actions for consistent dependency management.

- sample: https://x.com/omron_sinicx/status/1847150071143715312

## Contributions
Pull requests and bug reports are welcome. Feel free to [open issues](https://github.com/omron-sinicx/projectpage-template/issues)
