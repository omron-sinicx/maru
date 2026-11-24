import React from 'react';
import CorporateLogo from '@/components/logo.jsx';

export default class Authors extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    if (!this.props.affiliations) {
      return null;
    }
    const affiliationClass = `uk-width-1-${this.props.affiliations.length} uk-margin-small-top uk-text-bold uk-text-muted`;
    return (
      <div>
        <div
          className="uk-text-primary uk-text-center uk-grid-collapse"
          data-uk-grid
        >
          {this.props.affiliations.map((affiliation, idx) => {
            return (
              <span className={affiliationClass} key={'affiliation-' + idx}>
                <a
                  className="uk-link-heading"
                  href={affiliation.url}
                  target="_blank"
                >
                  {affiliation.name}
                </a>
              </span>
            );
          })}
          {/* one note per line: equal contribution, internship, joint last authors, ... */}
          {[].concat(this.props.meta ?? []).map((note, idx) => (
            <span className="uk-width-1-1" key={'meta-' + idx}>
              {note}
            </span>
          ))}
          <a
            className={`uk-width-1-${this.props.affiliations.length}@m`}
            href="https://www.omron.com/sinicx/"
            target="_blank"
          >
            <CorporateLogo
              name="sinicx"
              size="xl"
              inverted={this.props.theme == 'dark' ? true : false}
            />
          </a>
          <a
            className={`uk-width-1-${this.props.affiliations.length}@m`}
            href="https://lab.cluster.mu/"
            target="_blank"
          >
            <CorporateLogo name="cluster" size="xl" inverted={false} />
          </a>
          <a
            className={`uk-width-1-${this.props.affiliations.length}@m`}
            href="https://krkrpro.com/"
            target="_blank"
          >
            <CorporateLogo name="karakuri" size="xl" inverted={false} />
          </a>
        </div>
      </div>
    );
  }
}
