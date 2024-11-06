import React from 'react';
import { render } from 'react-dom';

export default class Authors extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const columnMaxLen =
      this.props.authors.length > 4 ? 3 : this.props.authors.length;
    const authorClass = `uk-width-1-${columnMaxLen} uk-width-1-${this.props.authors.length}@m`;
    const affliationClass = `uk-width-1-${this.props.affiliations.length} uk-margin-small-top uk-text-bold uk-text-muted`;
    return (
      <div>
        <div
          className="uk-text-primary uk-text-center uk-grid-collapse"
          data-uk-grid
        >
          {this.props.affiliations.map((affiliation, idx) => {
            return (
              <span className={affliationClass} key={'affiliation-' + idx}>
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
          <span className="uk-width-1-1">{this.props.meta}</span>
        </div>
      </div>
    );
  }
}
