// Static CSS imports so Vite extracts them into a <link> in <head> at build
// time. This is what fixes the FOUC: the stylesheet is render-blocking in the
// prerendered HTML instead of being loaded asynchronously after JS executes.
//
// `@active-theme` is a build-time alias resolved in vite.config.js to either
// `src/scss/theme.scss` or `src/scss/dark-theme.scss` based on `theme` in
// template.yaml. UIkit's JS (icons, slider, tooltip) is loaded lazily on the
// client by the components that need it, never here.
import '@active-theme';
import 'katex/dist/katex.min.css';
