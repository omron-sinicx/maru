import React from 'react';
import Authors from '../components/authors.jsx';
import { FaGithub, FaYoutube, FaMedium, FaRegFilePdf } from 'react-icons/fa6';
import { FaFilePdf } from 'react-icons/fa';
import { SiArxiv } from 'react-icons/si';
import { Icon } from '@iconify/react';

const HuggingFace = ({ size }) => (
  <Icon icon="logos:hugging-face-icon" style={{ fontSize: size }} />
);

const GoogleColab = ({ size }) => (
  <Icon icon="simple-icons:googlecolab" style={{ fontSize: size }} />
);

class ResourceBtn extends React.Component {
  constructor(props) {
    super(props);
    // Default for the static build (no `window`); corrected in componentDidMount.
    this.state = {
      isMobile: false,
    };
    this.icons = {
      paper: FaFilePdf,
      arxiv: SiArxiv,
      poster: FaRegFilePdf,
      code: FaGithub,
      video: FaYoutube,
      blog: FaMedium,
      demo: GoogleColab,
      huggingface: HuggingFace,
    };
    this.handleResize = this.handleResize.bind(this);
  }
  componentDidMount() {
    window.addEventListener('resize', this.handleResize);
    this.handleResize();
  }
  componentWillUnmount() {
    window.removeEventListener('resize', this.handleResize);
  }
  handleResize() {
    this.setState({ isMobile: window.innerWidth < 600 });
  }
  render() {
    if (!this.props.url) return null;
    const aClass = `uk-button uk-button-text uk-padding-remove ${this.props.rid === 0 ? 'uk-first-column' : 'uk-margin-medium-left@s uk-margin-small-left'}`;
    const sClass = 'uk-margin-small-left uk-margin-small-right uk-text-bold';
    const FaIcon = this.icons[this.props.title];
    const iTitle =
      this.props.title == 'huggingface' && this.state.isMobile
        ? ' hf '
        : this.props.title;
    return (
      <>
        <a className={aClass} href={this.props.url} target="_blank">
          <FaIcon size="2em" />
          <span className={sClass} style={{ fontFamily: 'Poppins' }}>
            {iTitle}
          </span>
        </a>
      </>
    );
  }
}

export default class Header extends React.Component {
  render() {
    const titleClass = `uk-${
      this.props.title.length > 15 ? 'h2' : 'h1'
    } uk-text-primary`;
    const baseStyle = this.props.header?.bg_image
      ? {
          backgroundImage: `url(${this.props.header.bg_image})`,
          backgroundSize: 'contain',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'left',
          backgroundColor: '#030706',
        }
      : null;
    // Set the curve as an inline `background-image` so its relative URL
    // resolves against the document (correct for root and subpath deploys).
    // Routing it through a CSS custom property instead would resolve the URL
    // against the extracted /assets/*.css stylesheet in the production build,
    // pointing at a nonexistent /assets/sinic_curve.png. Whether the curve (and
    // its side margin) actually render is still decided by a media query in
    // `_header.scss`, not by JS state — so the SSG markup and the hydrated
    // client match and the layout never shifts after mount.
    const curveStyle = this.props.header?.bg_curve
      ? { backgroundImage: `url(${this.props.header.bg_curve})` }
      : null;
    return (
      <>
        <div
          className="uk-cover-container uk-background-secondary"
          style={baseStyle}
        >
          <div className="header-curve" style={curveStyle}>
            <div className="uk-container uk-container-small uk-section">
              <div className="uk-text-center uk-text-bold">
                <p className={titleClass}>{this.props.title}</p>
              </div>
              <Authors
                authors={this.props.authors}
                affiliations={this.props.affiliations}
                meta={this.props.meta}
                theme={this.props.theme}
              />
              <div className="uk-flex uk-flex-center uk-margin-top">
                {Object.keys(this.props.resources).map((key) => (
                  <ResourceBtn
                    url={this.props.resources[key]}
                    title={key}
                    key={'header-' + key}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }
}
