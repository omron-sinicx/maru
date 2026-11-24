import React from 'react';

import { marked } from 'marked';
import markedKatex from 'marked-katex-extension';
marked.use(markedKatex({ throwOnError: false }));

export default class Overview extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <>
        <div
          className="uk-position-relative"
          data-uk-slideshow="autoplay:true; autoplay-interval:4000; animation:fade"
        >
          <div className="uk-slideshow-items">
            {this.props.slideshow.map((image, idx) => {
              return (
                <div key={'slide-' + idx}>
                  <img
                    src={image}
                    className="uk-align-center"
                    alt=""
                    data-uk-cover
                  />
                </div>
              );
            })}
          </div>
          <div className="uk-position-bottom-center uk-position-small uk-visible@s">
            <ul className="uk-thumbnav">
              {this.props.slideshow.map((image, idx) => {
                return (
                  <li data-uk-slideshow-item={idx} key={'thumb-' + idx}>
                    <a href="#">
                      <img src={image} width="100" height="67" alt="" />
                    </a>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      </>
    );
  }
}
