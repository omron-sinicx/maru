import React from 'react';
import { render } from 'react-dom';

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
            <div>
              <img
                src={require('../media/' + this.props.teaser)}
                className="uk-align-center"
                alt=""
                data-uk-cover
              />
            </div>
            <div>
              <img
                src={require('../media/sb_robot.png')}
                className="uk-align-center"
                alt=""
                data-uk-cover
              />
            </div>
            <div>
              <img
                src={require('../media/exploded_real_naname.jpg')}
                className="uk-align-center"
                alt=""
                data-uk-cover
              />
            </div>
            <div>
              <img
                src={require('../media/teaser.jpg')}
                className="uk-align-center"
                alt=""
                data-uk-cover
              />
            </div>
            <div>
              <img
                src="https://github.com/omron-sinicx/swarm-body/raw/main/images/maru_cradle.jpg"
                className="uk-align-center"
                alt=""
                data-uk-cover
              />
            </div>
          </div>
          <div className="uk-position-bottom-center uk-position-small">
            <ul className="uk-thumbnav">
              <li data-uk-slideshow-item="0">
                <a href="#">
                  <img
                    src={require('../media/' + this.props.teaser)}
                    width="100"
                    height="67"
                    alt=""
                  />
                </a>
              </li>
              <li data-uk-slideshow-item="1">
                <a href="#">
                  <img
                    src={require('../media/sb_robot.png')}
                    width="100"
                    height="67"
                    alt=""
                  />
                </a>
              </li>
              <li data-uk-slideshow-item="2">
                <a href="#">
                  <img
                    src={require('../media/exploded_real_naname.jpg')}
                    width="100"
                    height="67"
                    alt=""
                  />
                </a>
              </li>
              <li data-uk-slideshow-item="3">
                <a href="#">
                  <img
                    src={require('../media/teaser.jpg')}
                    width="100"
                    height="67"
                    alt=""
                  />
                </a>
              </li>
              <li data-uk-slideshow-item="4">
                <a href="#">
                  <img
                    src="https://github.com/omron-sinicx/swarm-body/raw/main/images/maru_cradle.jpg"
                    width="100"
                    height="67"
                    alt=""
                  />
                </a>
              </li>
            </ul>
          </div>
        </div>
      </>
    );
  }
}
