import React from 'react';
import {render} from 'react-dom';
import Authors from '../components/authors.jsx';

export default class Header extends React.Component {
  constructor(props) { super(props); }

  render() {
    return (
      <div className="uk-cover-container uk-background-secondary">
        <div className="uk-container uk-container-small uk-section">
          <div className="uk-text-center uk-text-bold">
            <p className="uk-h1 uk-text-primary">{this.props.title}</p>
            <span className="uk-label uk-label-primary uk-text-center uk-margin-bottom">{this.props.conference}</span>
          </div>
          <Authors authors={this.props.authors} affiliations={this.props.affiliations} />
          <div className="uk-flex uk-flex-center uk-margin-top">
            <a className="uk-button uk-button-text" href={this.props.paper} target="_blank">
              <span className="uk-icon" uk-icon="file-pdf" /> paper
            </a>
            <a className="uk-button uk-button-text uk-margin-medium-left" href={this.props.video} target="_blank">
              <span className="uk-icon" uk-icon="play-circle" /> video
            </a>
            <a className="uk-button uk-button-text uk-margin-medium-left" uk-tooltip="title: COMING SOON" href={this.props.code} target="_blank">
              <span className="uk-icon" uk-icon="github" /> code
            </a>
          </div>
        </div>
      </div>
    );
  }
}